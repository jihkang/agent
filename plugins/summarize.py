from scheme.mcp import MCPRequest, MCPRequestMessage
from plugin.base import BaseAgent

class SummaryPlugin(BaseAgent):
    name: str

    def __init__(self):
        self.name = self.plugin_name()

    @staticmethod
    def plugin_name():
        return "SummaryPlugin"
    
    async def run(self, query: str) -> MCPRequest[str]:
        if not query or not isinstance(query, str):
            return MCPRequest[str](content=[MCPRequestMessage[str](content="요약할 내용이 없습니다.")])
        
        # 매우 단순한 요약 예시: 첫 문장만 자르기
        summary = query.split(".")[0].strip()
        if not summary.endswith("."):
            summary += "."

        response = MCPRequest[str](
            content=[MCPRequestMessage[str](content=f"요약: {summary}")]
        )
        return response
