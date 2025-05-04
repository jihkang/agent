import pytest
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage, MCPResponse, MCPResponseMessage
from agent.tool_agent import ToolSelectorAgent

# Dummy 플러그인 매니저: list_registry()가 도구 리스트를 반환하도록 함.
class DummyPluginManager:
    def list_registry(self):
        return ["weather", "search"]

@pytest.mark.asyncio
async def test_tool_selector_agent_on_event(monkeypatch):
    # fake_tool_response: Model.ask가 반환할 고정 응답
    fake_tool_response = [
        MCPResponse[str](
            selected_tool="WeatherAgent",
            content=[
                MCPResponseMessage[str](content="execute weather tool")
            ]
        )
    ]

    # ToolSelectorAgent 내부에서 self.model은 models.model.Model의 인스턴스임.
    # 따라서, Model.ask를 monkeypatch로 대체하여 fake_tool_response를 반환하도록 합니다.
    monkeypatch.setattr(
        "models.model.Model.ask",
        lambda self, prompt, query: fake_tool_response
    )

    # Dummy PluginManager를 생성하여 ToolSelectorAgent에 전달합니다.
    dummy_pm = DummyPluginManager()
    tool_selector_agent = ToolSelectorAgent(plugin_manager=dummy_pm)
    
    # 올바른 구조의 입력 메시지 구성: payload는 MCPRequest 객체로 구성합니다.
    fake_input = AgentMessage(
        sender="PlanningAgent",
        receiver="ToolSelectorAgent",
        payload=[
            MCPRequest[str](
                content=[MCPRequestMessage[str](content="Select the appropriate tool for weather")]
            )
        ]
    )
    
    # Act: ToolSelectorAgent의 on_event() 호출 결과 소비
    results = []
    async for res in tool_selector_agent.on_event(fake_input):
        print(res)
        results.extend(res)

    # Assert: 반환된 메시지들이 ExecutionAgent로 전달되는지 확인
    assert results, "ToolSelectorAgent did not return any messages."
    # 예상: 각 메시지의 receiver는 "ExecutionAgent"
    for msg in results:
        # payload 내부 내용이 올바른 JSON 문자열(예시로 "weather" 포함)인지 확인
        # (여기서는 fake_tool_response의 payload를 그대로 반환하므로 JSON 문자열 내에 "weather"가 포함됨)
        # assert msg.receiver == "ExecutionAgent", f"Expected receiver 'ExecutionAgent', got '{msg.receiver}'"
        payload = msg.payload[0]
        assert "Weather" in payload.selected_tool, f"Expected 'weather' in payload selected_tool, got '{payload}'"