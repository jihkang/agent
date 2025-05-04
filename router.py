from collections.abc import AsyncGenerator
from typing import List
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from agent.tool_agent import ToolSelectorAgent
from agent.planning_agent import PlanningAgent
from agent.execution_agent import ExecutionAgent
from agent.validation_agent import ValidationAgent
from plugin.manager import PluginManager

from utils.logging import setup_logger
from utils.util import add_request  # 필요에 따라 로깅 모듈 사용

RECEIVER_PRIORITY = {
    "PlanningAgent": 1,
    "ToolSelectorAgent": 2,
    "ExecutionAgent": 3,
    "Router": 4,
    "user": 5,
    "fail": 6
}

SPECIAL_ROUTER = ["user", "Router"]

class Router:
    def __init__(self, plugin_manager: PluginManager):
        # 사용 가능한 에이전트 인스턴스들을 매핑
        self.agents = {
            "PlanningAgent": PlanningAgent(),
            "ToolSelectorAgent": ToolSelectorAgent(plugin_manager),
            "ExecutionAgent": ExecutionAgent(plugin_manager),
            "ValidationAgent": ValidationAgent(),
        }

        self.logger = setup_logger("Router")
    
    def route(self, agent_messages: List[AgentMessage]) -> List[AgentMessage]:
        # 우선순위 기준으로 정렬
        sorted_msgs = sorted(agent_messages, key=lambda m: RECEIVER_PRIORITY.get(m.receiver, 99))
        return sorted_msgs

    
    async def on_event(self, user_request: dict) -> AsyncGenerator[List[AgentMessage]]:
        """에이전트 메시지 루프를 실행하여 Generator[List[AgentMessage]] 형태로 결과를 순차 전달"""
        # 1. 사용자 요청을 기반으로 초기 메시지 생성 (PlanningAgent에 보낼 AgentMessage)
        initial_message = AgentMessage(
            sender="user", receiver="PlanningAgent",
            payload=[MCPRequest[str](content=[MCPRequestMessage[str](**user_request)])]
        )
        
        # 2. PlanningAgent를 호출하여 계획(step) 리스트를 생성
        plan_queue: List[AgentMessage] = []
        planning_maximum_count = 5

        try:
            # PlanningAgent.on_event는 Generator[List[AgentMessage]]를 반환
            async for plan_result in self.agents["PlanningAgent"].on_event(initial_message):
                # plan_result는 list 또는 AgentMessage 객체일 수 있음
                if isinstance(plan_result, list):
                    # 리스트인 경우 각 AgentMessage를 큐에 추가
                    plan_queue.extend(plan_result)
                elif isinstance(plan_result, AgentMessage):
                    # 단일 AgentMessage인 경우 큐에 추가
                    plan_queue.append(plan_result)
        except Exception as e:
            self.logger.error(f"PlanningAgent 처리 중 예외 발생: {e}", exc_info=True)
            # Planning 단계 실패 시 루프 중단
            return

        # 3. 계획된 각 단계를 순차적으로 실행
        while plan_queue:
            # ✅ 우선순위 정렬!
            msg: AgentMessage = plan_queue.pop(0)
            receiver = msg.receiver or ""
            try:
                if receiver == "user":
                    yield [msg]
                    continue
                
                if receiver == "Router":
                    # receiver 가 라우트일 경우는 크게 execution의 결과를 제외하면 없음.
                    # 이 때 결과를 판단하고, 이를 planning으로 합칠지, 아니면, 동작이 실패했음을 알리고, Pevious 의 Planning에 실패한 데이터로 남겨둘지 생각해야함.
                    yield [msg]
                    continue
                

                if receiver in self.agents:
                    agent = self.agents[receiver]

                    async for result in agent.on_event(msg):
                        if isinstance(result, list):
                            for sub_msg in result:
                                if isinstance(sub_msg, AgentMessage):
                                    if sub_msg.receiver in SPECIAL_ROUTER:
                                        yield [sub_msg]
                                        continue
                                    
                                    if receiver == "PlanningAgent":
                                        planning_maximum_count = max(planning_maximum_count - 1, 0)
                                        if planning_maximum_count == 0:
                                            continue
                                    
                                    if add_request(sub_msg):
                                        plan_queue.append(sub_msg)

                                    plan_queue = self.route(plan_queue)
                                    yield [sub_msg]  # 중간 결과 외부 출력 (디버그용)\
                           
                        elif isinstance(result, AgentMessage):
                            if result.receiver in SPECIAL_ROUTER:
                                yield [result]
                                continue
                            
                            if result.receiver == "PlanningAgent":
                                planning_maximum_count = max(planning_maximum_count - 1, 0)
                                if planning_maximum_count == 0:
                                    continue
                                                                                    
                            if add_request(result):
                                plan_queue.append(result)

                            plan_queue = self.route(plan_queue)
                            yield [result]

                else:
                    self.logger.error(f"알 수 없는 에이전트 '{receiver}' - 해당 단계 건너뜀")
                    continue

            except Exception as e:
                self.logger.error(f"{receiver} 처리 중 예외 발생: {e}", exc_info=True)
                continue