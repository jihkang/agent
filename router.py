import asyncio
from collections import deque
from collections.abc import AsyncGenerator
from copy import deepcopy
import datetime
from typing import Deque, Dict, List
from agent.planning_agent_mcts import PlanningState
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from agent.tool_agent import ToolSelectorAgent
from agent.planning_agent import PlanningAgent
from agent.execution_agent import ExecutionAgent
from agent.validation_agent import ValidationAgent
from plugin.manager import PluginManager
from utils.logging import setup_logger

RECEIVER_PRIORITY = {
    "PlanningAgent": 1,
    "ToolSelectorAgent": 2,
    "ExecutionAgent": 3,
    "Router": 4,
    "user": 5,
    "fail": 6
}

SPECIAL_ROUTER = ["user", "Router"]
MAX_ITERATIONS = 100

class Router:
    def __init__(self, plugin_manager: PluginManager):
        self.agents = {
            "PlanningAgent": PlanningAgent(),
            "ToolSelectorAgent": ToolSelectorAgent(plugin_manager),
            "ExecutionAgent": ExecutionAgent(plugin_manager),
            "ValidationAgent": ValidationAgent(),
        }
        self.logger = setup_logger("Router")
        self.sessions: Dict[str, PlanningState] = {}
        self.lock = asyncio.Lock()

    async def on_update_state(self, session_id: str, state: PlanningState):
        async with self.lock:
            self._update_session_state(session_id, state)

    async def on_event(self, user_request: dict, session_id: str = "default") -> AsyncGenerator[List[AgentMessage]]:
        initial_message = AgentMessage(
            sender="user", receiver="PlanningAgent",
            payload=[MCPRequest[str](content=[MCPRequestMessage[str](**user_request)])]
        )
        print(initial_message)
        async with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = PlanningState(
                    history=[], remaining_goals=[], execution_results=[]
                )

            state = deepcopy(self.sessions[session_id])
        self.agents["PlanningAgent"].set_state(state)

        plan_queue: Deque[AgentMessage] = deque()

        try:
            async for plan_result in self.agents["PlanningAgent"].on_event(initial_message):
                plan_result = plan_result if isinstance(plan_result, list) else [plan_result]    
                for new_plan in plan_result:
                    yield [new_plan]
                    plan_queue.append(new_plan)
        except Exception as e:
            self.logger.error(f"PlanningAgent 예외: {e}", exc_info=True)
            return
    
        self.sessions[session_id] = self.agents["PlanningAgent"].get_state()
        state = self.sessions[session_id]
        idx = 0
        while plan_queue:
            idx += 1
            if (idx > MAX_ITERATIONS):
                return 
            
            msg = plan_queue.popleft()
            receiver = msg.receiver or ""
            try:
                if receiver in SPECIAL_ROUTER:
                    self._update_session_state(session_id, state)
                    continue

                if receiver in self.agents:
                    agent = self.agents[receiver]
                    print(f"[Router] {receiver}의 on_event 호출 준비")
                    async for result in agent.on_event(msg):
                        print(f"[Router] {receiver}의 on_event 결과:", result)
                        result_list = result if isinstance(result, list) else [result]
                        yield result_list

                        for plan in result_list:
                            if not isinstance(plan, AgentMessage):
                                raise TypeError("[Router] Agent가 AgentMessage 아닌 객체를 반환했습니다.")
                            
                            if plan.sender == "ExecutionAgent":
                                state.set_result(plan.id, plan)
                            else:
                                state.set_history(plan)

                            if plan.receiver == "PlanningAgent":
                                plan_queue.append(plan)
                            else:
                                plan_queue.appendleft(plan)

                else:
                    self.logger.error(f"알 수 없는 receiver {receiver}")

            except Exception as e:
                self.logger.error(f"{receiver} 처리 중 에러: {e}", exc_info=True)
                yield [e]


    def _update_session_state(self, session_id: str, new_state: PlanningState):
        """세션 상태 병합 로직"""
        existing = self.sessions[session_id]
        existing.history = list({msg.id: msg for msg in existing.history + new_state.history}.values())
        existing.remaining_goals = [g for g in new_state.remaining_goals if g not in existing.history]
        existing.execution_results.extend(new_state.execution_results)
