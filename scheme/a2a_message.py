
from typing import List, Union
from pydantic import BaseModel

from scheme.mcp import MCPRequest, MCPResponse


class AgentMessage(BaseModel):
    sender: str = "user"
    receiver: str = "PlanningAgent"
    payload: List[Union[MCPResponse, MCPRequest]]