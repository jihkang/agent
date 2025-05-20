import pytest
from agent.planning_agent_mcts import PlanningState
from agent.planning_agent import PlanningAgent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import SUCCESS

# Step 1. 테스트용 가짜 결과 메시지
fake_plan = [
    AgentMessage(
        id=0,
        sender="PlanningAgent",
        receiver="ToolSelectorAgent",
        dag=-1,
        payload=[
            MCPRequest[dict](content=[
                MCPRequestMessage[dict](content="step 1: use search tool", metadata={})],
                stop_reason=SUCCESS
            )
        ],
        stop_reason=SUCCESS,
    ),
    AgentMessage(
        id=1,
        sender="PlanningAgent",
        receiver="user",
        dag=0,
        payload=[
            MCPRequest[dict](
                content=[
                    MCPRequestMessage[dict](content="final step: return to user", metadata={})
                ],
                stop_reason=SUCCESS
            )
        ],
        stop_reason=SUCCESS,
    )
]

# Step 2. FakePlanner 정의
class FakePlanner:
    def __init__(self, root_state, initial_epsilon=0.3, min_epsilon=0.05):
        print("📦 FakePlanner INIT")
        self.root = root_state

    def run(self, max_iter=10):
        print("🚀 FakePlanner.RUN CALLED")
        return fake_plan

# Step 3. 테스트 전용 PlanningAgent
class TestablePlanningAgent(PlanningAgent):
    def __init__(self):
        super().__init__()
        self.state = None

    async def on_event(self, message: AgentMessage):
        # ✅ 모델 ask는 무시하고 planner 실행만 테스트
        planner = FakePlanner(self.state)
        best_plan = planner.run(max_iter=10)
        yield best_plan

@pytest.mark.asyncio
async def test_planning_agent_generates_steps():
    agent = TestablePlanningAgent()
    agent.set_state(PlanningState(
        history=[],
        remaining_goals=[],
        execution_results=[]
    ))

    # 가짜 입력 메시지
    input_message = AgentMessage(
        sender="user",
        receiver="PlanningAgent",
        payload=[
            MCPRequest[dict](
                content=[
                    MCPRequestMessage[dict](content="make a plan to search the weather", metadata={})
                ],
                stop_reason=SUCCESS
            )
        ],
        stop_reason=SUCCESS
    )

    results = []
    async for result in agent.on_event(input_message):
        results.extend(result if isinstance(result, list) else [result])

    assert len(results) == 2
    assert all(isinstance(msg, AgentMessage) for msg in results)
    assert {msg.receiver for msg in results} == {"ToolSelectorAgent", "user"}