
import os
from llama_cpp import Any
import requests
from plugin.base import BaseAgent
from scheme.mcp import MCPRequest, MCPResponse, MCPResponseMessage
from utils.env import load_dotenv
from utils.logging import setup_logger

class WeatherToolAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.logger = setup_logger("weather_tool_agent")
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.api_url = "http://api.openweathermap.org/data/2.5/weather"

    # """ weather info """
    @staticmethod
    def plugin_name():
        return f"WeatherToolAgent"

    async def run(self, input_data):
        try:
            if not hasattr(input_data, "content"):
                raise ValueError("리퀘스트가 비었습니다.")
    
            request_content = input_data.content  # Assuming single message
        
            # 도시 이름 추출
            city = request_content["city"]
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "kr" 
            }
            
            if self.api_key == "":
                weather = "맑음"
                temp = "22"
                content = f"{city}의 현재 날씨는 '{weather}', 온도는 {temp}°C입니다."
            else:
                response = requests.get(self.api_url, params=params)
                if response.status_code != 200:
                    content = f"날씨 정보를 가져오는 데 실패했습니다. 상태코드: {response.status_code}"
                else:
                    data = response.json()
                    weather = data['weather'][0]['description']
                    temp = data['main']['temp']
                    content = f"{city}의 현재 날씨는 '{weather}', 온도는 {temp}°C입니다."

            mcp_response_msg = MCPResponseMessage[str](content=content)
            return MCPResponse[str](content=[mcp_response_msg], dag= -1)
        except Exception as e:
            self.logger.error(f"WeatherToolAgent 오류: {e}", exc_info=True)
            error_response = MCPResponseMessage[str](content="날씨 정보를 처리하는 도중 오류가 발생했습니다.")
            return MCPResponse[str](content=[error_response], dag = -1)