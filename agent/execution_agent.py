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

    def _extract_failure_reason(self, plugin_response: MCPRequest[Any]) -> str:
        if not plugin_response.content:
            return "plugin response is empty"

        first = plugin_response.content[0]
        return first.content if hasattr(first, "content") else "plugin failed"

    def _build_retry_message(
        self,
        source_message: AgentMessage,
        plugin_name: str,
        plan: MCPRequestMessage[Any],
        failure_reason: str,
        stop_reason: str,
    ) -> AgentMessage:
        retry_payload = MCPRequest[dict](
            content=[
                MCPRequestMessage[dict](
                    content=plan.content,
                    metadata={
                        "selected_tool": plugin_name,
                        "failure_reason": failure_reason,
                        "retry_hint": "select better tool or refine parameters",
                    },
                )
            ],
            selected_tool=plugin_name,
            stop_reason=stop_reason,
        )

        return AgentMessage(
            sender="ExecutionAgent",
            receiver="ToolSelectorAgent",
            id=source_message.id,
            payload=[retry_payload],
            origin_request=source_message.origin_request,
            dag=source_message.id,
            stop_reason=stop_reason,
        )

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[AgentMessage]:
        try:
            for payload in message.payload:
                plugin_name = payload.selected_tool
                content_list = payload.content

                if not plugin_name:
                    raise ValueError("Plugin이 선택되지 않았습니다.")

                for plan in content_list:
                    plugin_response = await self.plugin_manager.run(plugin_name, plan)

                    if plugin_response.stop_reason != SUCCESS:
                        failure_reason = self._extract_failure_reason(plugin_response)
                        stop_reason = plugin_response.stop_reason or MORE_DATA
                        yield self._build_retry_message(
                            source_message=message,
                            plugin_name=plugin_name,
                            plan=plan,
                            failure_reason=failure_reason,
                            stop_reason=stop_reason,
                        )
                        continue

                    yield AgentMessage(
                        origin_request=message.origin_request,
                        sender="ExecutionAgent",
                        receiver="Router",
                        id=message.id,
                        dag=message.dag,
                        payload=[plugin_response],
                        stop_reason=SUCCESS,
                    )

        except Exception as e:
            self.logger.error(f"ExecutionAgent 에러: {e}", exc_info=True)
            response_message = MCPRequestMessage[dict](
                content="ExecutionAgent 처리 중 시스템 오류가 발생했습니다.", metadata={}
            )
            response_payload = MCPRequest[dict](content=[response_message], selected_tool="")
            yield AgentMessage(
                sender="ExecutionAgent",
                receiver="user",
                payload=[response_payload],
                id=message.id,
                dag=message.dag,
                origin_request=message.origin_request,
                stop_reason=FAIL,
            )
