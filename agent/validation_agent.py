from collections.abc import AsyncGenerator

from agent.selector.base import Agent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, MAX_RETRIES, MORE_DATA, RETRY
from utils.logging import setup_logger


class ValidationAgent(Agent):
    """Execution 결과를 검증하고 재시도 전략을 결정하는 에이전트."""

    def __init__(self):
        self.logger = setup_logger("ValidationAgent")

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[AgentMessage]:
        if not message.payload:
            yield self._failure_message(message, "검증할 실행 결과가 비어 있습니다.")
            return

        result = message.payload[0]
        stop_reason = result.stop_reason

        if stop_reason != MORE_DATA:
            # 검증할 이슈가 없으면 현재 메시지를 그대로 전달
            yield message
            return

        if message.retries >= MAX_RETRIES:
            yield self._failure_message(
                message,
                f"필수 파라미터 수집 재시도 횟수({MAX_RETRIES})를 초과했습니다.",
            )
            return

        feedback_content = ""
        feedback_metadata = {}
        if result.content:
            feedback_content = result.content[0].content
            feedback_metadata = result.content[0].metadata or {}

        retry_payload = MCPRequest[dict](
            content=[
                MCPRequestMessage[dict](
                    content=f"{feedback_content}\n누락 파라미터를 채워 도구를 다시 선택하세요.",
                    metadata=feedback_metadata,
                )
            ],
            selected_tool=result.selected_tool,
            stop_reason=RETRY,
        )

        yield AgentMessage(
            id=message.id,
            dag=message.dag,
            sender="ValidationAgent",
            receiver="ToolSelectorAgent",
            retries=message.retries + 1,
            origin_request=message.origin_request,
            payload=[retry_payload],
            stop_reason=RETRY,
        )

    def _failure_message(self, message: AgentMessage, reason: str) -> AgentMessage:
        payload = MCPRequest[dict](
            content=[MCPRequestMessage[dict](content=reason, metadata={})],
            stop_reason=FAIL,
        )
        return AgentMessage(
            id=message.id,
            dag=message.dag,
            sender="ValidationAgent",
            receiver="user",
            payload=[payload],
            origin_request=message.origin_request,
            retries=message.retries,
            stop_reason=FAIL,
        )
