from abc import ABC
from typing import Generic, Literal, Optional, Union
from pydantic import BaseModel, field_validator
from validator.validate import isValid, T


class MCPMessage(BaseModel):
    """ mcp protocol """
    role: str
    type: str = "text"
    content: Union[str, dict]

    @field_validator('type')
    def is_valid(cls, v):
        if not isValid(v):
            raise ValueError(f"Invalid message type: {v}")
        
        return v


class MCPResponse(BaseModel, Generic[T]):
    """ mcp response """
    type: str
    content: T


