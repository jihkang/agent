import pytest
from agent.planning_agent import PlanningAgent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.util import merge_agent_messages


def test_merge_agent_message():
    msg1 = AgentMessage(
        id=1,
        sender="user",
        receiver="PlanningAgent",
        dag=1,
        retries=1,
        payload=[
            MCPRequest(
                content=[
                    MCPRequestMessage(
                        role="user",
                        content={"city": "Seoul", "temp": 22}
                    )
                ]
            )
        ]
    )
    msg2 = AgentMessage(
        id=2,
        sender="user",
        receiver="PlanningAgent",
        dag=2,
        retries=2,
        payload=[
            MCPRequest(
                content=[
                    MCPRequestMessage(
                        type="result",
                        content={"weather": "Clear"}
                    )
                ]
            )
        ]
    )

    merged_msg = merge_agent_messages(msg1, msg2)

    assert merged_msg.sender == "user"
    assert merged_msg.receiver == "PlanningAgent"
    assert merged_msg.dag == 2
    assert merged_msg.retries == 2
    assert len(merged_msg.payload) == 1
    print("Test passed.")
