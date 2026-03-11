import random
from copy import deepcopy
from typing import Dict, List, Union

from scheme.a2a_message import AgentMessage
from utils.constant import FAIL, SUCCESS


class PlanningState:
    history: List[AgentMessage] = []
    remaining_goals: List[AgentMessage] = []
    execution_results: Dict[int, List[AgentMessage]] = {}

    def __init__(
        self,
        history: List[AgentMessage],
        remaining_goals: List[AgentMessage],
        execution_results: Dict[str, List[AgentMessage]] = {},
    ):
        self.history = history
        self.remaining_goals = remaining_goals
        self.execution_results = execution_results

    def clone(self) -> "PlanningState":
        return PlanningState(
            history=deepcopy(self.history),
            remaining_goals=deepcopy(self.remaining_goals),
            execution_results=deepcopy(self.execution_results),
        )

    def init_args(self, **kwargs):
        self.__dict__.update(kwargs)

    def set_history(self, result: Union[AgentMessage | List[AgentMessage]]):
        if isinstance(result, list):
            self.history.extend(result)
            return

        self.history.append(result)

    def set_goals(self, result: Union[AgentMessage | List[AgentMessage]]):
        if isinstance(result, list):
            self.remaining_goals.extend(result)
            return

        self.remaining_goals.append(result)

    def set_result(self, parent_id: int, result: AgentMessage):
        if not parent_id in self.execution_results:
            self.execution_results[parent_id] = []

        state = self.execution_results[parent_id]

        if result in state:
            print(f"[set_result] Duplicate detected — skipping")
            return

        self.execution_results[parent_id].append(result)

    def update_execute(self, new_state: Dict[int, List[AgentMessage]]):
        for k, v in new_state.items():
            if k in self.execution_results:
                for value in v:
                    if value not in self.execution_results[k]:
                        self.execution_results[k].extend(v)
            else:
                self.execution_results[k] = v

    def pop_result(self, parent_id: int, remove_message: AgentMessage):
        if not parent_id in self.execution_results:
            return

        self.execution_results[parent_id].remove(remove_message)

    def get_result_failure(self, parent_id: int) -> AgentMessage | None:
        if not parent_id in self.execution_results:
            return None

        list_result = self.execution_results.get(parent_id, [])

        for p in list_result:
            if p.stop_reason == FAIL:
                return p

        return None

    def get_result(self, parent_id: int) -> List[AgentMessage]:
        if parent_id == -1 or not parent_id in self.execution_results:
            return []

        return self.execution_results[parent_id]

    def get_success_all_results(self, key: int = -5) -> List[AgentMessage]:
        result = []
        for k, v in self.execution_results.items():
            if key == -5:
                result.extend(v)
            elif key == k:
                result.extend(v)

        return result


def evaluate_plan(history: List[AgentMessage]) -> float:
    if not history:
        return 0.0

    score = -0.2 * len(history)

    success_steps = [step for step in history if step.stop_reason == SUCCESS]
    fail_steps = [step for step in history if step.stop_reason == FAIL]

    score += len(success_steps) * 1.0
    score -= len(fail_steps) * 2.0

    if history[-1].receiver == "user":
        score += 3.0

    tool_usage = set(step.receiver for step in history)
    score += len(tool_usage) * 0.5

    return score


class MCTSPlanner:
    def __init__(self, root_state: PlanningState, initial_epsilon: float = 0.3, min_epsilon: float = 0.05):
        self.root = root_state
        self.initial_epsilon = initial_epsilon
        self.min_epsilon = min_epsilon

    def run(self, max_iter: int = 100) -> List[AgentMessage]:
        best_plan: List[AgentMessage] = []
        best_score = float("-inf")

        for i in range(max_iter):
            epsilon = max(self.min_epsilon, self.initial_epsilon * (1 - i / max_iter))
            state = self.root.clone()
            score = self.simulate(state, epsilon)
            if score > best_score:
                best_score = score
                best_plan = deepcopy(state.history)

        # planner 결과를 현재 상태에 반영
        self.root.history = deepcopy(best_plan)
        planned_ids = {msg.id for msg in best_plan if msg.id is not None}
        self.root.remaining_goals = [
            goal for goal in self.root.remaining_goals if goal.id not in planned_ids
        ]

        return best_plan

    def _ready_goal_indexes(self, state: PlanningState, executed_ids: set[int]) -> List[int]:
        ready_indexes: List[int] = []
        for idx, goal in enumerate(state.remaining_goals):
            if goal.dag in (-1, None) or goal.dag in executed_ids:
                ready_indexes.append(idx)
        return ready_indexes

    def simulate(self, state: PlanningState, epsilon: float) -> float:
        executed_ids = {msg.id for msg in state.history if msg.id is not None}

        while state.remaining_goals:
            ready_indexes = self._ready_goal_indexes(state, executed_ids)
            if not ready_indexes:
                break

            if random.random() < epsilon:
                chosen_idx = random.choice(ready_indexes)
            else:
                chosen_idx = min(
                    ready_indexes,
                    key=lambda idx: state.remaining_goals[idx].id
                    if state.remaining_goals[idx].id is not None
                    else 10**9,
                )

            next_step = state.remaining_goals.pop(chosen_idx)
            state.history.append(next_step)
            if next_step.id is not None:
                executed_ids.add(next_step.id)

        return evaluate_plan(state.history)
