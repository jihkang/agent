import os
import requests
from plugin.base import BaseAgent
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, MORE_DATA, SUCCESS
from utils.env import load_dotenv
from utils.logging import setup_logger

class WeatherToolAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        load_dotenv()
        self.logger = setup_logger("weather_tool_agent")
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "")
        self.api_url = "http://api.openweathermap.org/data/2.5/weather"

    @staticmethod
    def plugin_name():
        return f"WeatherToolAgent"

    async def run(self, input_data: MCPRequestMessage):
        try:
            request = input_data.content
            metadata = input_data.metadata
            missing = {}

            print("Weather plugin=================")
            print(request, metadata)
            print("===============================")

            try:
                city = metadata["city"]
            except Exception:
                city = None

            if not city:
                missing["city"] = "string"
                raise ValueError(missing)

            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",
                "lang": "en"  # changed to 'en' for English descriptions
            }

            if self.api_key == "":
                # Fallback response
                weather = "Clear"
                temp = "22"
                content = {
                    "content": f"The current weather in {city} is '{weather}', with a temperature of {temp}°C.",
                    "city": city,
                    "weather": weather,
                    "temp": temp,
                }
            else:
                response = requests.get(self.api_url, params=params)
                if response.status_code != 200:
                    content = {
                        "content": f"Failed to retrieve weather information. Status code: {response.status_code}",
                        "city": city
                    }
                else:
                    data = response.json()
                    weather = data['weather'][0]['description']
                    temp = data['main']['temp']
                    content = {
                        "content": f"The current weather in {city} is '{weather}', with a temperature of {temp}°C.",
                        "city": city,
                        "weather": weather,
                        "temp": temp
                    }

            mcp_response_msg = MCPRequestMessage[dict](content=request, metadata=content)
            return MCPRequest[dict](content=[mcp_response_msg], selected_tool=self.plugin_name(), stop_reason=SUCCESS)

        except ValueError as v:
            self.logger.error(f"WeatherToolAgent error: {v}", exc_info=True)
            response = MCPRequestMessage(content=request, metadata=metadata)
            return MCPRequest[dict](content=[response], selected_tool=self.plugin_name(), stop_reason=MORE_DATA)

        except Exception as e:
            self.logger.error(f"WeatherToolAgent error: {e}", exc_info=True)
            error_response = MCPRequestMessage[dict](
                content="An error occurred while processing weather information.",
                metadata={}
            )
            return MCPRequest[dict](content=[error_response], selected_tool=self.plugin_name(), stop_reason=FAIL)