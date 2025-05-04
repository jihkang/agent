from collections.abc import AsyncGenerator
import os
import logging
import random
from typing import List
from copy import deepcopy
from agent.selector.base import Agent
from models.model import ApiModel, Model
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPResponse, MCPResponseMessage
from utils.env import load_dotenv
from utils.logging import setup_logger


class PlanningState:
    def __init__(self, current_step: int, history: List[AgentMessage], remaining_goals: List[AgentMessage]):
        self.current_step = current_step
        self.history = history  # 이미 처리된 step (AgentMessage 리스트)
        self.remaining_goals = remaining_goals  # 아직 처리 안 된 step (AgentMessage 리스트)

def simulate(state: PlanningState) -> float:
    while state.remaining_goals:
        next_step = state.remaining_goals.pop(0)
        state.history.append(next_step)
    return evaluate_plan(state.history)

def evaluate_plan(history: List[AgentMessage]) -> float:
    score = 0

    # 1. 전체 길이(짧을수록 좋음)
    score -= len(history)

    # 2. user로 끝나면 추가 보너스
    if history and history[-1].receiver == "user":
        score += 5

    # 3. fail receiver가 있으면 큰 패널티
    if any(step.receiver == "fail" for step in history):
        score -= 10

    # 4. PlanningAgent와 ExecutionAgent 조합이 다양할수록 보너스
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
            progress = i / max_iter
            # adaptive epsilon 적용
            epsilon = max(self.min_epsilon, self.initial_epsilon * (1 - progress)) 

            state = deepcopy(self.root)
            score = self.simulate(state, epsilon)
            if score > best_score:
                best_score = score
                best_plan = state.history

        return best_plan

    def simulate(self, state: PlanningState, epsilon: float) -> float:
        while state.remaining_goals:
            if random.random() < epsilon:
                idx = random.randint(0, len(state.remaining_goals) - 1)
                next_step = state.remaining_goals.pop(idx)
            else:
                next_step = state.remaining_goals.pop(0)

            state.history.append(next_step)

        return evaluate_plan(state.history)

class PlanningAgent(Agent):
    model: Model

    def __init__(self):
        self.system_prompt = """
         You are a PlanningAgent. Your job is to analyze user input and generate JSON-structured planning steps using predefined tools.

        Available receivers:
        - "PlanningAgent" : "planning steps"
        - "ToolSelectorAgent" : "select the appropriate tool for a given task"
        - "user" : "final response to the user"

        Your job is to:
        1. Analyze the user's natural language request.
        2. Break the task into step-by-step plans.
        3. For each step, choose **one** receiver from:
        - "PlanningAgent" (for further planning)
        - "ToolSelectorAgent" (for task execution selection)
        - "user" (if this step is the final response to the user).

        Return ONLY a JSON array in the following format:

        [
        {
            "receiver": "<one of 'PlanningAgent', 'ToolSelectorAgent', 'user'>",
            "payload": [{"content": "자연어로 된 단계 설명"}]
        },
        ...
        ]

        Only output the JSON array. Do not include any explanations or introductions.
        """
        self.logger = setup_logger("PlanningAgent")
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        self.model = ApiModel("gemini", api_key, "gemini-2.0-flash-lite")

        
    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        try:
            for payload in message.payload:
                content_data = payload.content
                if isinstance(content_data, list):
                    queries = [item.content for item in content_data]
                else:
                    queries = [content_data.content]

                for query in queries:
                    if not query:
                        response_message = MCPResponseMessage[str](content="플래닝 결과가 존재하지 않습니다.")
                        response_payload = MCPResponse[str](content=[response_message])
                        yield [AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])]
                        return

                    response_messages = self.model.ask(self.system_prompt, query, request_sender="PlanningAgent")
                    if not response_messages:
                        response_message = MCPResponseMessage[str](content="플래닝 결과가 비어 있습니다.")
                        response_payload = MCPResponse[str](content=[response_message])
                        yield [AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])]
                        return
                    # 2. PlanningState 초기화
                    root_state = PlanningState(current_step=0, history=[], remaining_goals=response_messages)

                    # 3. MCTS 실행
                    planner = MCTSPlanner(root_state)
                    best_plan = planner.run(max_iter=100)
                    
                    yield best_plan

        except Exception as e:
            self.logger.error(f"PlanningAgent 에러: {e}", exc_info=True)
            response_message = MCPResponseMessage[str](content="플래닝 중 시스템 오류가 발생했습니다.")
            response_payload = MCPResponse[str](content=[response_message])
            yield [AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])]
