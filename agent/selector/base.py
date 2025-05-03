
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from scheme.a2a_message import AgentMessage
from typing import List


class Agent(ABC):
    @abstractmethod
    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        pass