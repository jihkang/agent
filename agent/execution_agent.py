from collections.abc import AsyncGenerator
from typing import Final, List
from agent.selector.base import Agent
from plugin.manager import PluginManager
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage, MCPResponse, MCPResponseMessage
from utils.logging import setup_logger

class ExecutionAgent(Agent):
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.logger = setup_logger("ExecutionAgent")


    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        try:
            for payload in message.payload:
                if not payload:
                    continue 
            
                content_data = payload.content
                tasks: Final[str] = ""
                if isinstance(content_data, list):
                    tasks = "".join([item.content for item in content_data])
                else:
                    tasks = content_data.content

                result = []
            
                # 툴이름은 tool selector가 제공한 데이터를 실행 해주는것 으로 진행 
                plugin_name = payload.selected_tool  # 또는 message.receiver, 네 설계에 맞게

                # MCPRequest 생성
                request = MCPRequest[str](content=[MCPRequestMessage[str](content=tasks)])
                
                # 플러그인 실행
                plugin_response = self.plugin_manager.run(plugin_name, request)

                # 결과 전달
                # 🔥 결과를 유저에게 넘길 때는 무조건 MCPResponse로 감싸야 함
                if isinstance(plugin_response, MCPRequest):
                    # 실행 결과가 MCPRequest형태로 잘못 온 경우 강제 변환 (혹시모를 대비)
                    final_payload = MCPResponse[str](content=[MCPResponseMessage[str](content=plugin_response.content)])
                else:
                    final_payload = plugin_response  # 정상 Response라면 그대로

                result.append(
                    AgentMessage(
                        sender="ExecutionAgent",
                        receiver="Router",
                        payload=[final_payload]  # 반드시 Response로 보내기
                    )
                )

                yield result

        except Exception as e:
            self.logger.error(f"ExecutionAgent 에러: {e}", exc_info=True)
            response_message = MCPResponseMessage[str](content="ExecutionAgent 처리 중 시스템 오류가 발생했습니다.")
            response_payload = MCPResponse[str](content=[response_message])
            yield [AgentMessage(sender="ExecutionAgent", receiver="user", payload=[response_payload])]