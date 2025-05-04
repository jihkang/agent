import pytest
from agent.planning_agent import PlanningAgent
from scheme.a2a_message import AgentMessage

@pytest.mark.asyncio
async def test_planning_agent_generates_plan():
    # Arrange
    # 예시: 사용자 요청 메시지 생성 (실제 AgentMessage의 필드에 맞게 수정)
    input_message = AgentMessage(
        sender="User",
        recipient="PlanningAgent",
        payload={"request": "generate plan for task X"}
    )
    agent = PlanningAgent()  # 필요 시 초기화 인자 추가

    # Act
    # on_event가 비동기 제너레이터 형태라면 아래와 같이 결과 메시지를 리스트에 담는다.
    results = []
    async for msg in agent.on_event(input_message):
        results.append(msg)
    
    # Assert
    # 결과 메시지가 반환되었는지 확인
    assert len(results) > 0, "PlanningAgent가 어떤 메시지도 생성하지 않았습니다."

    for msg in results:
        print(msg)