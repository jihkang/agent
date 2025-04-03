from abc import ABC, abstractmethod
from typing import List
from core.mcp import MCPMessage, MCPResponse

class BaseLLM(ABC):
    """LLM 기본 인터페이스"""
    @abstractmethod
    async def generate(self, messages: List[MCPMessage]) -> MCPResponse:
        pass
    
    @abstractmethod
    async def load_model(self):
        pass 