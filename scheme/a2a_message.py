
from typing import Any, List, Optional, Union
from pydantic import BaseModel
from scheme.mcp import MCPRequest, MCPResponse


class AgentMessage(BaseModel):
    id: Optional[int] = None
    sender: str = "user"
    receiver: str = "PlanningAgent"
    payload: List[Union[MCPResponse[Any], MCPRequest[Any]]]