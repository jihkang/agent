
from typing import Any, List, Optional
from pydantic import BaseModel
from scheme.mcp import MCPRequest


class AgentMessage(BaseModel):
    id: Optional[int] = None
    sender: str = "user"
    receiver: str = "PlanningAgent"
    dag: Optional[int] = -1
    retries: int = 0
    payload: List[MCPRequest[Any]]
    origin_request: str = ""
    stop_reason: str = ""
