from scheme.mcp import MCPResponse, MCPResponseMessage
from plugin.base import BaseAgent

class SummaryPlugin(BaseAgent):
    name = "summary"

    @staticmethod
    def plugin_name():
        return "Summarizes a given paragraph into a short sentence."
    
    def run(self, query: str) -> MCPResponse[str]:
        if not query or not isinstance(query, str):
            return MCPResponse[str](content=[MCPResponseMessage[str](content="요약할 내용이 없습니다.")])
        
        # 매우 단순한 요약 예시: 첫 문장만 자르기
        summary = query.split(".")[0].strip()
        if not summary.endswith("."):
            summary += "."

        response = MCPResponse[str](
            content=[MCPResponseMessage[str](content=f"요약: {summary}")]
        )
        return response
