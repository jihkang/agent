import pytest
from agent.planning_agent import PlanningAgent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage, MCPResponse, MCPResponseMessage

@pytest.mark.asyncio
async def test_planning_agent_generates_steps(monkeypatch):
    # Arrange: ApiModel.ask를 모킹하여 LLM 응답을 강제로 지정
    fake_response = [
        AgentMessage(
            sender="PlanningAgent",
            receiver="ToolSelectorAgent",
            payload=[
                MCPResponse[str](content=[
                    MCPResponseMessage[str](content="step 1: use search tool")
                ])
            ]
        ),
        AgentMessage(
            sender="PlanningAgent",
            receiver="user",
            payload=[
                MCPResponse[str](content=[
                    MCPResponseMessage[str](content="final step: return to user")
                ])
            ]
        )
    ]

    # monkeypatch를 사용하여 model.ask를 고정된 fake_response로 대체
    monkeypatch.setattr("agent.planning_agent.ApiModel.ask", lambda *args, **kwargs: fake_response)

    agent = PlanningAgent()
    input_message = AgentMessage(
        sender="user",
        receiver="PlanningAgent",
        payload=[
            MCPRequest[str](content=[
                MCPRequestMessage[str](content="make a plan to search the weather")
            ])
        ]
    )

    # Act
    results = []
    async for result in agent.on_event(input_message):
        results.extend(result)

    # Assert
    assert len(results) == 2
    for msg in results:
        assert isinstance(msg, AgentMessage)
        assert msg.receiver in {"ToolSelectorAgent", "user"}