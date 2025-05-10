from plugin.base import BaseAgent
from scheme.mcp import MCPRequest, MCPRequest, MCPRequestMessage
from utils.constant import FAIL, MORE_DATA, SUCCESS
from utils.logging import setup_logger

class ScheduleRecommenderAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.logger = setup_logger("schedule_recommend_agent")

    @staticmethod
    def plugin_name():
        return "ScheduleRecommenderAgent"

    async def run(self, input_data: MCPRequestMessage):
        try:
            print("=========Recommend===============")
            print(input_data)
            print('=================================')
            request = input_data.content  # dict형 데이터
            metadata = input_data.metadata
            missing = {}
            
            try:
                city = metadata["city"]
            except Exception as e:
                city = None
            try:
                weather = metadata["weather"]
            except Exception as e:
                weather = None

            if city is None:
                missing["city"] = "string"
            
            if weather is None:
                missing["weather"] = "string"

            if len(missing.keys()) > 0:
                print(f"[DEBUG] error on {missing}")
                raise ValueError(missing)
            
            # 📝 Recommend schedule based on weather
            if "rain" in weather or "snow" in weather:
                recommended_time = "2:00 PM"
                activity = "Indoor activities (e.g., museum, café)"
            elif "cloudy" in weather:
                recommended_time = "1:00 PM"
                activity = "Light walk or reading"
            else:
                recommended_time = "11:00 AM"
                activity = "Outdoor activities (e.g., park, biking)"

            content = (
                f"The current weather in {city} is '{weather}'.\n"
                f"Recommended time: {recommended_time}\n"
                f"Recommended activity: {activity}"
            )
            metadata = {
                "city": city,
                "recommended_time": recommended_time,
                "activity": activity
            }

            response = MCPRequestMessage[dict](content=content, metadata=metadata)
            return MCPRequest[dict](content=[response], stop_reason=SUCCESS)
        
        except ValueError as v:
            print(v)
            metadata = v
            response = MCPRequest(content=request, metadata=metadata)
            return MCPRequest[dict](content=[response], selected_tool=self.plugin_name(), stop_reason=MORE_DATA)
        except Exception as e:
            print(e)
            error_response = MCPRequestMessage[str](content="An error occurred while generating the schedule.")
            return MCPRequest[str](content=[error_response], selected_tool=self.plugin_name(), stop_reason=FAIL)