import pytest

from agent.execution_agent import ExecutionAgent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, SUCCESS


class DummyPluginManager:
    def __init__(self, response: MCPRequest[dict]):
        self.response = response

    async def run(self, name, request):
        return self.response


@pytest.mark.asyncio
async def test_execution_agent_success_path():
    plugin_response = MCPRequest[dict](
        content=[MCPRequestMessage[dict](content="ok", metadata={})],
        stop_reason=SUCCESS,
    )
    agent = ExecutionAgent(plugin_manager=DummyPluginManager(plugin_response))

    message = AgentMessage(
        id=1,
        sender="ToolSelectorAgent",
        receiver="ExecutionAgent",
        payload=[
            MCPRequest[dict](
                selected_tool="WeatherToolAgent",
                content=[MCPRequestMessage[dict](content="weather", metadata={})],
            )
        ],
    )

    results = []
    async for item in agent.on_event(message):
        results.append(item)

    assert len(results) == 1
    assert results[0].receiver == "Router"
    assert results[0].stop_reason == SUCCESS


@pytest.mark.asyncio
async def test_execution_agent_failure_generates_retry_feedback():
    plugin_response = MCPRequest[dict](
        content=[MCPRequestMessage[dict](content="missing city", metadata={})],
        stop_reason=FAIL,
    )
    agent = ExecutionAgent(plugin_manager=DummyPluginManager(plugin_response))

    message = AgentMessage(
        id=7,
        sender="ToolSelectorAgent",
        receiver="ExecutionAgent",
        payload=[
            MCPRequest[dict](
                selected_tool="WeatherToolAgent",
                content=[MCPRequestMessage[dict](content="weather", metadata={})],
            )
        ],
    )

    results = []
    async for item in agent.on_event(message):
        results.append(item)

    assert len(results) == 1
    assert results[0].receiver == "ToolSelectorAgent"
    assert results[0].payload[0].content[0].metadata["failure_reason"] == "missing city"
    assert results[0].stop_reason == FAIL
