from typing import Generic, List, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")
U = TypeVar("U")

class MCPRequestMessage(GenericModel, Generic[T]):
    role: str
    content: T


class MCPResponseMessage(GenericModel, Generic[U]):
    type: str
    text: U
    

class MCPRequest(GenericModel, Generic[U]):
    """ default mcp response """
    model: str
    messages: List[MCPRequestMessage[T]]
    max_tokens: int
    system: str


class MCPResponse(GenericModel, Generic[U]):
    """ defulat mcp request """
    model: str
    id: str
    content: List[MCPResponseMessage[U]]
    stop_reason: str
