from typing import Any, Dict
from plugin.base import BaseAgent
from scheme.mcp import MCPResponse, MCPResponseMessage

class ReserveAgent(BaseAgent):
    description = "테스트 에이전트"
    version = "1.1"

    @staticmethod
    def plugin_name():
        return f"ReserveAgent"
    
    
    def run(self, data: Dict[str, Any]) -> Any:
        print("today reserve : ", data)
        return MCPResponse[str](
            content=[
                MCPResponseMessage[str](content="9시에 예약을 진행하겠습니다.")
            ]
        )