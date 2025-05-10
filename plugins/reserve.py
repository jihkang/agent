from typing import Any, Dict
from plugin.base import BaseAgent
from scheme.mcp import MCPRequest, MCPRequestMessage

class ReserveAgent(BaseAgent):
    description = "테스트 에이전트"
    version = "1.1"

    @staticmethod
    def plugin_name():
        return f"ReserveAgent"
    
    
    async def run(self, input_data) -> Any:
        print("today reserve : ", input_data)
        
        return MCPRequest[dict](
            content=[
                MCPRequestMessage[dict](content="9시에 예약을 진행하겠습니다.", metadata={**input_data.metadata})
            ]
        )