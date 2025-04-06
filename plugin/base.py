from abc import ABC, abstractmethod
from typing import Any, Dict


# will be change Dict to Request and return will be changed Response
class BaseAgent(ABC):
    description: str = "No description available"
    version: str = "1.0"
    _execution_count: int = 0

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
    def run(self, input_data: Dict[str, Any]) -> Any:
        pass