from collections.abc import AsyncGenerator
from copy import deepcopy
import os
from typing import List
from agent.planning_agent_mcts import MCTSPlanner, PlanningState
from agent.selector.base import Agent
from models.model import ApiModel
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.env import load_dotenv
from utils.logging import setup_logger


class PlanningAgent(Agent):
    model: ApiModel
    state: PlanningState

    def __init__(self):
        self.system_prompt = """
            You are a task planner agent for an AI assistant. Your goal is to break down the user's high-level request into smaller actionable steps for specialized agents.

            **Rules**:
            1. **Step Requirements**:
            - `id`: Unique integer starting from 0 and incrementing for each step.
            - `receiver`: One of ["ToolSelectorAgent", "PlanningAgent", "user"].
            - `dag`: If the step depends on a previous step, set the `dag` field to the `id` of that step. Otherwise, use id
            - `payload`: A list of MCPRequestMessage objects with at least one message. Each message must have:
                - `role`: Always "user".
                - `content`: The specific task description.
                - `metadata`: To solve this step need parameter 

            2. **Response Format**:
            Return a list of AgentMessage objects following this JSON structure:

            ```json
            {
            "id": 0,
            "sender": "PlanningAgent",
            "receiver": "ToolSelectorAgent",
            "dag": -1,
            "payload": [{
                "role": "user",
                "content": "location info seongdong-gu",
                "metadata": {
                    "city" : "seongdong-gu",
                }
            }]
            },
            {
            "id": 1,
            "sender": "PlanningAgent",
            "receiver": "ToolSelectorAgent",
            "dag": 0,
            "payload": [{
                "role": "user",
                "content": "seongdong-gu weather information",
                "metadata": {
                    "city" : "seongdong-gu"
                }
            }]
            },
            {
            "id": 2,
            "sender": "PlanningAgent",
            "receiver": "user",
            "dag": 1,
            "payload": [{
                "role": "user",
                "content": "recommendation schedule with weather",
                "metadata": {},
            }]
            }
        """

        self.logger = setup_logger("PlanningAgent")
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        self.model = ApiModel("gemini", api_key, "gemini-2.0-flash-lite")

    def set_state(self, state: PlanningState) -> None:
        self.state = state

    def get_state(self) -> PlanningState:
        return self.state

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[AgentMessage]:
        try:
            for payload in message.payload:
                content_data = payload.content
                if isinstance(content_data, list):
                    queries = [item.content for item in content_data]
                else:
                    queries = [content_data.content]

                for query in queries:
                    if not query:
                        response_message = MCPRequestMessage[str](content="플래닝 결과가 존재하지 않습니다.")
                        response_payload = MCPRequest[str](content=[response_message])
                        yield AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])
                        return

                response_messages = await self.model.ask(self.system_prompt, queries, request_sender="PlanningAgent")
                if not response_messages:
                    response_message = MCPRequestMessage[str](content="플래닝 결과가 비어 있습니다.")
                    response_payload = MCPRequest[str](content=[response_message])
                    
                    yield AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])
                    return
                
                self.state.remaining_goals.extend(response_messages)
                # 2. MCTS 실행
                planner = MCTSPlanner(root_state=self.state)
                best_plan = planner.run(max_iter=10)
                
                for plan in best_plan:
                    yield plan

        except Exception as e:
            self.logger.error(f"PlanningAgent 에러: {e}", exc_info=True)
            response_message = MCPRequestMessage[str](content="플래닝 중 시스템 오류가 발생했습니다.")
            response_payload = MCPRequest[str](content=[response_message])
            yield AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload], stop_reason="failure")
