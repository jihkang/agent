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
    selected_tool: Optional[str] = None
    max_tokens: int = 256
    system: str = ""


class MCPResponse(GenericModel, Generic[U]):
    """ defulat mcp request """
    model: str = ""
    id: str = "0"
    content: List[MCPResponseMessage[U]] | MCPResponseMessage[U]
    selected_tool: Optional[str] = None
    stop_reason: str = "done"
