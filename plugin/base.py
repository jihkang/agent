from abc import ABC, abstractmethod
from typing import Any, Dict, List

from scheme.mcp import T, MCPRequest


# will be change Dict to Request and return will be changed Response
class BaseAgent(ABC):
    description: str = "No description available"
    version: str = "1.0"
    _execution_count: int = 0

    def __init__(self):
        self.state: Dict[str, List[MCPRequest[T]]] = {}

    def increment_count(self) -> None:
        """이 Agent 인스턴스의 클래스 카운트를 +1 증가"""
        self.__class__._execution_count += 1

    @classmethod
    def get_count(cls) -> int:
        return cls._execution_count

    @staticmethod
    @abstractmethod
    def plugin_name() -> str:
        pass
    
    @abstractmethod
    async def run(self, input_data:Any):
        """ 실행 메서드"""
        pass
  
    def push_state(self, role: str, response: MCPRequest[T]) -> None:
        if (role not in self.state):
            self.state[role] = []
        
        self.state[role].append(response)

    def get_histroy(self, role: str) -> List[MCPRequest[T]]:
        return self.state.get("role", [])

    def clear(self):
        self.state.clear()
