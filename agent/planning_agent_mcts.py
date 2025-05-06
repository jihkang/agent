import random
from typing import Any, Dict, List
from scheme.a2a_message import AgentMessage

class PlanningState:
    history: List[AgentMessage]
    remaining_goals: List[AgentMessage]
    execution_results: Dict[str, List[AgentMessage]]

    def __init__(self, history: List[AgentMessage],
            remaining_goals: List[AgentMessage], execution_results: Dict[str, List[AgentMessage]]):
        self.history = history
        self.remaining_goals = remaining_goals
        self.execution_results = execution_results

    def set_history(self, result: AgentMessage):
        self.history.append(result)

    def set_result(self, parent_id: str, result: AgentMessage):
        self.execution_results.get(parent_id, []).append(result)

    def get_result(self, parent_id: str) -> List[AgentMessage]:
        if (parent_id == "-1"):
            return []
        
        return self.execution_results[parent_id]

    def get_dag_prompt(self, dag: str) -> str:
        contents = [
            element  # 최종 문자열 요소
            for msg in self.execution_results.get(dag, [])
            for item in msg.payload.content  # payload.content 순회
            for content in item.content       # content.content 순회 (리스트)
            for element in content            # content.content 내 각 요소 순회
        ]

        return "".join(contents)
    

def evaluate_plan(history: List[AgentMessage]) -> float:
    score = -len(history)
    if history and history[-1].receiver == "user":
        score += 5
    if any(step.receiver == "fail" for step in history):
        score -= 10
    tool_usage = set(step.receiver for step in history)
    score += len(tool_usage)
    return score

class MCTSPlanner:
    def __init__(self, root_state: PlanningState, initial_epsilon: float = 0.3, min_epsilon: float = 0.05):
        self.root = root_state
        self.initial_epsilon = initial_epsilon
        self.min_epsilon = min_epsilon

    def run(self, max_iter: int = 100) -> List[AgentMessage]:
        best_plan = []
        best_score = float('-inf')

        for i in range(max_iter):
            epsilon = max(self.min_epsilon, self.initial_epsilon * (1 - i / max_iter))
            state = self.root
            score = self.simulate(state, epsilon)
            if score > best_score:
                best_score = score
                best_plan = state.history

        return best_plan

    def simulate(self, state: PlanningState, epsilon: float) -> float:

        while state.remaining_goals:
            idx = random.randint(0, len(state.remaining_goals) - 1) if random.random() < epsilon else 0
            next_step = state.remaining_goals.pop(idx)
            state.history.append(next_step)
            
        return evaluate_plan(state.history)