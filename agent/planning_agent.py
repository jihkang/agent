from collections.abc import AsyncGenerator
from copy import deepcopy
import os
from typing import List
from agent.planning_agent_mcts import MCTSPlanner, PlanningState
from agent.selector.base import Agent
from models.model import ApiModel
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPResponse, MCPResponseMessage
from utils.env import load_dotenv
from utils.logging import setup_logger


class PlanningAgent(Agent):
    model: ApiModel
    state: PlanningState

    def __init__(self):
        self.system_prompt = """
            **Role**: You are an expert DAG Planner for multi-agent systems.  
            **Goal**: Decompose user requests into atomic steps with precise dependencies.
            **Must include previous step ID
            **Rules**:
            1. **Step Requirements**:
            - `id`: Unique integer (0-start)
            - `receiver`: "PlanningAgent", "ToolSelectorAgent", or "user"
            - `payload`: [{"content": "task", "dag": parent_id}]

            2. **DAG Construction**:
            - Each step must depend on the **earliest possible parent**
            - No circular dependencies allowed
            - Leaf nodes must end with "user"

            3. **Validation Checklist**:
            ✅ All `dag` values reference existing IDs  
            ✅ No disconnected subgraphs  
            ✅ Minimum 2 steps, maximum 8 steps

            **Examples**:

            **Case 1 - Simple**:
            Input: {"content": "성동구 날씨 알려줘"}
            Output:
            [
            {"id":0, "receiver":"ToolSelectorAgent", "payload":[{"content":"성동구 위도 조회", "dag":-1}]},
            {"id":1, "receiver":"ToolSelectorAgent", "payload":[{"content":"성동구 날씨 조회", "dag":0}]},
            {"id":2, "receiver":"user", "payload":[{"content":"최종 결과", "dag":1}]}
            ]

            **Case 2 - Complex**:
            Input: {"content": "서울에서 가장 가까운 공항 날씨 비교"}
            Output:
            [
            {"id":0, "receiver":"ToolSelectorAgent", "payload":[{"content":"서울 좌표 조회", "dag":-1}]},
            {"id":1, "receiver":"ToolSelectorAgent", "payload":[{"content":"주변 공항 목록 조회", "dag":0}]},
            {"id":2, "receiver":"ToolSelectorAgent", "payload":[{"content":"각 공항 좌표 조회", "dag":1}]},
            {"id":3, "receiver":"ToolSelectorAgent", "payload":[{"content":"각 공항 날씨 조회", "dag":2}]},
            {"id":4, "receiver":"PlanningAgent", "payload":[{"content":"날씨 데이터 비교", "dag":3}]},
            {"id":5, "receiver":"user", "payload":[{"content":"비교 결과", "dag":4}]}
            ]
        """

        self.logger = setup_logger("PlanningAgent")
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        self.model = ApiModel("gemini", api_key, "gemini-2.0-flash-lite")

    def set_state(self, state: PlanningState) -> None:
        self.state = state

    def get_state(self) -> PlanningState:
        return self.state

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

                response_messages = await self.model.ask(self.system_prompt, queries, request_sender="PlanningAgent")
                if not response_messages:
                    response_message = MCPResponseMessage[str](content="플래닝 결과가 비어 있습니다.")
                    response_payload = MCPResponse[str](content=[response_message])
                    
                    yield [AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])]
                    return
                
                self.state.remaining_goals.extend(response_messages)
                # 2. MCTS 실행
                planner = MCTSPlanner(root_state=self.state)
                best_plan = planner.run(max_iter=10)
                
                yield best_plan

        except Exception as e:
            self.logger.error(f"PlanningAgent 에러: {e}", exc_info=True)
            response_message = MCPResponseMessage[str](content="플래닝 중 시스템 오류가 발생했습니다.")
            response_payload = MCPResponse[str](content=[response_message])
            yield [AgentMessage(sender="PlanningAgent", receiver="user", payload=[response_payload])]
