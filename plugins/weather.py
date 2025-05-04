
import os
import requests
from collections.abc import AsyncGenerator
from typing import List

from agent.selector.base import Agent
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage, MCPResponse, MCPResponseMessage
from utils.env import load_dotenv
from utils.logging import setup_logger

class WeatherToolAgent(Agent):
    def __init__(self):
        load_dotenv()
        self.logger = setup_logger("weather_tool_agent")
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.api_url = "http://api.openweathermap.org/data/2.5/weather"

    # """ weather info """
    @staticmethod
    def plugin_name():
        return f"weather agent"


    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        try:
            for payload in message.payload:
                if isinstance(payload, MCPRequest):
                    request_content = payload.content[0].content  # Assuming single message

                    # 도시 이름 추출
                    city = request_content.strip()
                    params = {
                        "q": city,
                        "appid": self.api_key,
                        "units": "metric",
                        "lang": "kr"
                    }

                    response = requests.get(self.api_url, params=params)
                    if response.status_code != 200:
                        content = f"날씨 정보를 가져오는 데 실패했습니다. 상태코드: {response.status_code}"
                    else:
                        data = response.json()
                        weather = data['weather'][0]['description']
                        temp = data['main']['temp']
                        content = f"{city}의 현재 날씨는 '{weather}', 온도는 {temp}°C입니다."

                    mcp_response_msg = MCPResponseMessage[str](content=content)
                    response_payload = MCPResponse[str](content=[mcp_response_msg])
                    yield [AgentMessage(sender="WeatherToolAgent", receiver="user", payload=[response_payload])]
        except Exception as e:
            self.logger.error(f"WeatherToolAgent 오류: {e}", exc_info=True)
            error_response = MCPResponseMessage[str](content="날씨 정보를 처리하는 도중 오류가 발생했습니다.")
            yield [AgentMessage(sender="WeatherToolAgent", receiver="user", payload=[MCPResponse[str](content=[error_response])])]