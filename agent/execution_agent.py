from collections.abc import AsyncGenerator
from typing import Any
from agent.selector.base import Agent
from plugin.manager import PluginManager
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, MORE_DATA, SUCCESS
from utils.logging import setup_logger

class ExecutionAgent(Agent):
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.logger = setup_logger("ExecutionAgent")


    async def on_event(self, message: AgentMessage) -> AsyncGenerator[AgentMessage]:
        try:
            for payload in message.payload:
                # 툴이름은 tool selector가 제공한 데이터를 실행 해주는것 으로 진행 
                plugin_name = payload.selected_tool
                content_list = payload.content
                if not plugin_name:
                    raise ValueError("Plugin이 선택되지 않았습니다.")

                # 플러그인 실행
                for plan in content_list:
                    plugin_response = await self.plugin_manager.run(plugin_name, plan)
                    
                    if plugin_response.stop_reason != SUCCESS:
                        print(plugin_response.stop_reason)
                        request_message = AgentMessage(
                            sender = "ExecutionAgent",
                            receiver = "ToolSelectorAgent",
                            id = message.id,
                            payload = MCPRequest[dict](
                                content=[MCPRequestMessage[dict](
                                    content = plan.content,
                                    metadata = {},
                                )],
                                selected_tool = plugin_name,
                            ),
                            origin_request=message.origin_request,
                            dag = message.id,
                            stop_reason=plugin_response.stop_reason,
                        )
                        yield request_message
                        continue             
                        
                    final_payload = plugin_response  # 정상 Response라면 그대로
                    yield AgentMessage(
                            origin_request=message.origin_request,
                            sender="ExecutionAgent",
                            receiver="Router",
                            id = message.id,
                            dag = message.dag,
                            payload=[final_payload],
                            stop_reason=SUCCESS
                        )
                
        except Exception as e:
            self.logger.error(f"ExecutionAgent 에러: {e}", exc_info=True)
            response_message = MCPRequestMessage[dict](content="ExecutionAgent 처리 중 시스템 오류가 발생했습니다.", metadata={})
            response_payload = MCPRequest[dict](content=[response_message], selected_tool="", )
            yield AgentMessage(
                sender="ExecutionAgent",
                receiver="user",
                payload=[response_payload],
                id=message.id,
                dag=message.dag,
                origin_request=message.origin_request,
                stop_reason = FAIL
            )