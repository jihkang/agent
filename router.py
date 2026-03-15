import asyncio
from collections import deque
from collections.abc import AsyncGenerator
from copy import deepcopy
import datetime
from typing import Deque, Dict
from agent.planning_agent_mcts import PlanningState
from agent.selector.base import Agent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from agent.tool_agent import ToolSelectorAgent
from agent.planning_agent import PlanningAgent
from agent.execution_agent import ExecutionAgent
from agent.validation_agent import ValidationAgent
from plugin.manager import PluginManager
from utils.constant import FAIL, MAX_RETRIES, SPECIAL_ROUTER, SUCCESS
from utils.logging import setup_logger
from utils.util import merge_metadata_only

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

    async def route(self, plan_queue: Deque[AgentMessage], msg: AgentMessage, receiver: str, state: PlanningState):
        agent = self.agents[receiver]

        try:
            async for result in agent.on_event(msg):
                print(f"[Router] {receiver}의 on_event 결과:", result)
                
                # result가 비었을 경우 처리 
                if not result:
                    continue
    
                if isinstance(result, AgentMessage):
                    yield result
                    self._process_agent_message(result, plan_queue, msg, state)
                else:
                    self.logger.warning(f"[Router] 예상치 못한 결과 타입: {type(result)}")

        except Exception as e:
            import traceback
            self.logger.error(f"{receiver} route 처리 중 에러: {e}")
            self.logger.error(traceback.format_exc())
            
            # 에러 응답 생성
            response_message = MCPRequestMessage[dict](content=f"에러 발생: {str(e)}", metadata={})
            response_payload = MCPRequest[dict](content=[response_message])
            error_msg = AgentMessage(
                sender=receiver, 
                receiver="user", 
                id=msg.id,
                payload=[response_payload],
                retries=0,
                dag=-msg.dag,
                stop_reason=FAIL
            )
            yield error_msg
            
    def _process_agent_message(self, plan: AgentMessage, plan_queue: Deque[AgentMessage], msg: AgentMessage, state: PlanningState):
        """AgentMessage 처리 로직을 분리하여 코드 중복을 방지합니다."""
        if not plan.payload or len(plan.payload) == 0:
            print("[Router] payload 비어있음. 스킵:", plan)
            return
        
        stop_reason = getattr(plan.payload[0], "stop_reason", "")
        if plan.sender == "ExecutionAgent":
            print(stop_reason, plan.payload)
            if stop_reason == FAIL:
                return

            state.set_result(plan.id, plan)
            
            if stop_reason == SUCCESS:
                need_more_msg = state.get_result_failure(msg.id)
                
                if need_more_msg is not None:
                    plan_queue.appendleft(need_more_msg)
                    state.pop_result(msg.id, need_more_msg)
            return

        if plan.sender == "ValidationAgent":
            if plan.stop_reason == FAIL:
                return

            if plan.receiver in SPECIAL_ROUTER:
                return

            plan_queue.appendleft(plan)
            return
        else:
            state.set_history(plan)
            if plan.receiver in SPECIAL_ROUTER:
                return  # 🔥 user, Router인 경우 더 이상 진행 안 함
            elif plan.receiver == "PlanningAgent":
                plan_queue.append(plan)
            else:
                plan_queue.appendleft(plan)

    async def on_event(self, user_request: dict, session_id: str = "default") -> AsyncGenerator[AgentMessage]:
        print(user_request["content"])
        initial_message = AgentMessage(
            sender="user", receiver="PlanningAgent",
            origin_request = user_request["content"],
            payload=[MCPRequest[dict](content=[MCPRequestMessage[dict](**user_request)])]
        )
        print(initial_message)
        async with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = PlanningState(
                    history=[], remaining_goals=[], execution_results={}
                )

            state = deepcopy(self.sessions[session_id])
            self.agents["PlanningAgent"].set_state(state)

        plan_queue: Deque[AgentMessage] = deque()

        try:
            async for plan_result in self.agents["PlanningAgent"].on_event(initial_message):
                plan_result = plan_result if isinstance(plan_result, list) else [plan_result]
                for new_plan in plan_result:
                    # new_plan이 리스트인 경우 처리
                    if isinstance(new_plan, list):
                        for item in new_plan:
                            if isinstance(item, AgentMessage):
                                if item.receiver == "user":
                                    # yield item
                                    continue
                                plan_queue.append(item)
                    else:
                        if new_plan.receiver == "user":
                            continue
                        plan_queue.append(new_plan)
        except Exception as e:
            self.logger.error(f"PlanningAgent 예외: {e}", exc_info=True)
            return
        print(plan_queue)
        self.sessions[session_id] = self.agents["PlanningAgent"].get_state()
        state = self.sessions[session_id]
        
        cur = datetime.datetime.now()
        print(f"start time : {cur}")
        while plan_queue:
            try:
                msg = plan_queue.popleft()
                
                # ✅ 리스트라면 flatten (이전 플랜 결과가 잘못 들어간 경우 대응)
                while isinstance(msg, list):
                    if not msg:
                        msg = None
                        break  # <- continue가 아니라 loop 탈출
                    for m in reversed(msg[1:]):
                        plan_queue.appendleft(m)
                    msg = msg[0]
                
                if msg == None:
                    continue

                receiver = msg.receiver
                if msg.retries > MAX_RETRIES:
                    print(msg)
                    raise Exception(f"요청이 {MAX_RETRIES}회 이상 실패하였습니다. 다시 시도해주세요.")

                combined_msg = msg
                if msg.dag != -1:
                    previous_msg = state.get_result(msg.dag)

                    if len(previous_msg) == 0:
                        msg.retries += 1
                        plan_queue.append(msg)
                        continue
                     
                    combined_msg = merge_metadata_only(previous_msg[-1], msg)
                
                print("[Before Router]===================")
                print(combined_msg)
                print("==================================")

                if receiver in SPECIAL_ROUTER:
                    self._update_session_state(session_id, state)
                    continue

                if receiver in self.agents:
                    print(f"[Router] {receiver}의 on_event 호출 준비")
                    async for step_result in self.route(plan_queue, combined_msg, receiver, state):
                        self._update_session_state(session_id, state)
                        
                        yield step_result

                else:
                    self.logger.error(f"알 수 없는 receiver {receiver}")

                end = datetime.datetime.now()
                if end - cur > datetime.timedelta(minutes=3):
                    raise Exception("너무 오래지속 되는것으로 판단하고 종료 합니다.")

            except Exception as e:
                self.logger.error(f"{receiver} 처리 중 에러: {e}", exc_info=True)
                response_message = MCPRequestMessage(content=f"에러 발생: {str(e)}", metadata = {})
                response_payload = MCPRequest(content=[response_message])
                yield AgentMessage(sender=receiver, receiver="user", payload=[response_payload], stop_reason=FAIL)
        
        print("[done]")

    def _update_session_state(self, session_id: str, new_state: PlanningState):
        """세션 상태 병합 로직"""
        existing = self.sessions[session_id]
        
        existing.init_args(
            history=list({msg.id: msg for msg in existing.history + new_state.history}.values()),
            remaining_goals = [g for g in new_state.remaining_goals if g not in existing.history]
        ) 
        existing.update_execute(new_state.execution_results)
