from typing import Generic, List, Optional, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")
U = TypeVar("U")

class MCPRequestMessage(GenericModel, Generic[T]):
    role: str = "user"
    content: T

class MCPResponseMessage(GenericModel, Generic[U]):
    type: str = ""
    content: U


class MCPRequest(GenericModel, Generic[T]):
    """ default mcp response """
    model: str = ""
    content: List[MCPRequestMessage[T]] | MCPRequestMessage[T]
    dag: int = -1
    selected_tool: Optional[str] = None
    origin_request: str = ""
    max_tokens: int = 256
    system: str = ""


class MCPResponse(GenericModel, Generic[U]):
    """ defulat mcp request """
    model: str = ""
    content: List[MCPResponseMessage[U]] | MCPResponseMessage[U]
    dag: int = -1
    selected_tool: Optional[str] = None
    origin_request: str = ""
    stop_reason: str = "done"