
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from scheme.a2a_message import AgentMessage


class Agent(ABC):
    @abstractmethod
    async def on_event(self, message: AgentMessage) -> AsyncGenerator[AgentMessage]:
        pass