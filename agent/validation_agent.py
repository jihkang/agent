# validation_agent.py
from collections.abc import AsyncGenerator
from typing import List
from agent.selector.base import Agent
from scheme.a2a_message import AgentMessage

class ValidationAgent(Agent):
    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        return 