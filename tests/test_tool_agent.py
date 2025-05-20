import pytest
from unittest.mock import AsyncMock
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from agent.tool_agent import ToolSelectorAgent
from utils.constant import SUCCESS

class DummyPluginManager:
    def list_registry(self):
        return ["WeatherToolAgent", "SearchToolAgent"]

    def pair_registry_execute_info(self):
        return [
            "WeatherToolAgent - Returns current weather and temperature for a given city.",
            "SearchToolAgent - Performs web searches based on user queries."
        ]

@pytest.mark.asyncio
async def test_tool_selector_agent_on_event(monkeypatch):
    fake_tool_response = [
        MCPRequest[dict](
            selected_tool="WeatherToolAgent",
            content=[
                MCPRequestMessage[dict](content="execute weather tool", metadata={})
            ],
            stop_reason=SUCCESS,
        )
    ]

    # AsyncMock을 사용하여 비동기 함수 모킹
    monkeypatch.setattr(
        "models.model.Model.ask",
        AsyncMock(return_value=fake_tool_response)
    )

    dummy_pm = DummyPluginManager()
    tool_selector_agent = ToolSelectorAgent(plugin_manager=dummy_pm)

    fake_input = AgentMessage(
        sender="PlanningAgent",
        receiver="ToolSelectorAgent",
        payload=[
            MCPRequest[dict](
                content=[MCPRequestMessage[dict](content="Select the appropriate tool for weather", metadata={})],
                stop_reason=SUCCESS,
            ),
        ],
        stop_reason=SUCCESS,
    )

    results = []
    async for res in tool_selector_agent.on_event(fake_input):
        results.append(res)

    assert results, "ToolSelectorAgent did not return any messages."
    for msg in results:
        payload = msg.payload[0]
        assert "Weather" in payload.selected_tool, f"Expected 'Weather' in payload selected_tool, got '{payload.selected_tool}'"
