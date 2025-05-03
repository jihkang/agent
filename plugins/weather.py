from typing import Any, Dict
from plugin.base import BaseAgent
from scheme.mcp import MCPRequest, MCPResponse, MCPResponseMessage

class WeatherAgent(BaseAgent):
    """ weather info """

    @staticmethod
    def plugin_name():
        return f"weather agent"
    
    
    def run(self, data: MCPRequest[Any]) -> MCPResponse[Any]:
        print("today reserve : ", data)
        message = MCPResponse[str](
            content=[
                MCPResponseMessage[str](content="9시에 비가 올 예정입니다")
            ]
        )
        return message