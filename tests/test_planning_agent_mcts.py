from agent.planning_agent_mcts import MCTSPlanner, PlanningState, evaluate_plan
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, SUCCESS


def _msg(step_id: int, dag: int, receiver: str = "ToolSelectorAgent", stop_reason: str = SUCCESS):
    return AgentMessage(
        id=step_id,
        sender="PlanningAgent",
        receiver=receiver,
        dag=dag,
        payload=[MCPRequest[dict](content=[MCPRequestMessage[dict](content=f"step-{step_id}", metadata={})])],
        stop_reason=stop_reason,
    )


def test_mcts_planner_respects_dag_order():
    goals = [_msg(1, 0), _msg(0, -1), _msg(2, 1, receiver="user")]
    state = PlanningState(history=[], remaining_goals=goals, execution_results={})
    planner = MCTSPlanner(state, initial_epsilon=0.0, min_epsilon=0.0)

    best_plan = planner.run(max_iter=3)

    assert [m.id for m in best_plan] == [0, 1, 2]


def test_evaluate_plan_penalizes_failures():
    success_plan = [_msg(0, -1, stop_reason=SUCCESS), _msg(1, 0, receiver="user", stop_reason=SUCCESS)]
    failure_plan = [_msg(0, -1, stop_reason=FAIL), _msg(1, 0, receiver="user", stop_reason=SUCCESS)]

    assert evaluate_plan(success_plan) > evaluate_plan(failure_plan)
