from plugin.base import BaseAgent
from scheme.mcp import MCPRequest, MCPResponse, MCPResponseMessage

class ScheduleRecommenderAgent(BaseAgent):
    @staticmethod
    def plugin_name():
        return "ScheduleRecommenderAgent"

    async def run(self, input_data):
        try:
            request = input_data.content  # dict형 데이터
            print("=========Recommend===============")
            print(request)
            print('=================================')

            missing = {}
            city = request.get("city", None)
            if city is None:
                missing["city"] = "string"
            weather = request.get("weather", None)
            if weather is None:
                missing["weather"] = "string"

            if len(missing.keys()) > 0:
                print(f"[DEBUG] error on {missing}")
                raise ValueError(missing)
            
            # 📝 날씨에 맞춰 추천 일정
            if "비" in weather or "눈" in weather:
                recommended_time = "오후 2시"
                activity = "실내 활동 (미술관, 카페)"
            elif "흐림" in weather:
                recommended_time = "오후 1시"
                activity = "가벼운 산책 또는 독서"
            else:
                recommended_time = "오전 11시"
                activity = "야외 활동 (공원, 자전거 타기)"

            content = (
                f"{city}의 현재 날씨는 '{weather}'입니다.\n"
                f"추천 일정 시간: {recommended_time}\n"
                f"추천 활동: {activity}"
            )
        except ValueError as v:
            content = v
            response = MCPRequest(content=content)
            return MCPResponse[dict](content=[response], dag=-1, stop_reason="failure")
        
        response = MCPResponseMessage[str](content=content)
        return MCPResponse[str](content=[response], dag=-1)