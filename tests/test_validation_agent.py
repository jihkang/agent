import pytest

from agent.validation_agent import ValidationAgent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, MAX_RETRIES, MORE_DATA, RETRY, SUCCESS


@pytest.mark.asyncio
async def test_validation_agent_retries_when_more_data_needed():
    agent = ValidationAgent()
    message = AgentMessage(
        id=7,
        sender="ExecutionAgent",
        receiver="ValidationAgent",
        dag=3,
        retries=1,
        payload=[
            MCPRequest[dict](
                content=[
                    MCPRequestMessage[dict](
                        content="weather tool needs city",
                        metadata={"city": "string"},
                    )
                ],
                selected_tool="WeatherToolAgent",
                stop_reason=MORE_DATA,
            )
        ],
        stop_reason=MORE_DATA,
    )

    results = []
    async for result in agent.on_event(message):
        results.append(result)

    assert len(results) == 1
    retry_message = results[0]
    assert retry_message.receiver == "ToolSelectorAgent"
    assert retry_message.retries == 2
    assert retry_message.stop_reason == RETRY
    assert retry_message.payload[0].content[0].metadata == {"city": "string"}


@pytest.mark.asyncio
async def test_validation_agent_fails_after_max_retries():
    agent = ValidationAgent()
    message = AgentMessage(
        id=9,
        sender="ExecutionAgent",
        receiver="ValidationAgent",
        dag=2,
        retries=MAX_RETRIES,
        payload=[
            MCPRequest[dict](
                content=[MCPRequestMessage[dict](content="need city", metadata={"city": "string"})],
                selected_tool="WeatherToolAgent",
                stop_reason=MORE_DATA,
            )
        ],
    )

    results = []
    async for result in agent.on_event(message):
        results.append(result)

    assert len(results) == 1
    failure_message = results[0]
    assert failure_message.receiver == "user"
    assert failure_message.stop_reason == FAIL


@pytest.mark.asyncio
async def test_validation_agent_passthrough_when_success():
    agent = ValidationAgent()
    message = AgentMessage(
        id=3,
        sender="ExecutionAgent",
        receiver="ValidationAgent",
        dag=0,
        payload=[
            MCPRequest[dict](
                content=[MCPRequestMessage[dict](content="done", metadata={})],
                selected_tool="WeatherToolAgent",
                stop_reason=SUCCESS,
            )
        ],
    )

    results = []
    async for result in agent.on_event(message):
        results.append(result)

    assert len(results) == 1
    assert results[0] == message
