from typing import Generic, List, Optional, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")

class MCPRequestMessage(GenericModel, Generic[T]):
    role: str = "user"
    content: str
    metadata: T 

class MCPRequest(GenericModel, Generic[T]):
    content: List[MCPRequestMessage[T]]
    selected_tool: Optional[str] = None
    max_tokens: int = 256
    system: str = ""
    stop_reason:str = ""