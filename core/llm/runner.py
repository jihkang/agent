from typing import Union, List
from pydantic import BaseModel
from core.mcp import MCPMessage, MCPResponse
from core.llm.local_llm import LocalLLM

class LLMConfig(BaseModel):
    model_type: str  # "local" 또는 "api"
    model_path: str  # 로컬 모델 경로
    temperature: float = 0.7
    max_tokens: int = 1000

class LLMRunner:
    def __init__(self, config: LLMConfig):
        self.config = config
        if config.model_type == "local":
            self.llm = LocalLLM(config.model_path)
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {config.model_type}")
        
    async def run(self, messages: List[MCPMessage]) -> MCPResponse:
        return await self.llm.generate(messages) 