import asyncio
from core.llm.local_llm import LocalLLM
from core.llm.runner import LLMRunner, LLMConfig
from core.plugin import PluginManager
from core.agent import Agent
from core.mcp import MCPMessage

async def main():
    # LLM 설정
    config = LLMConfig(
        model_type="local",
        # 한국어 모델 예시 (선택 가능)
        # model_path="beomi/KoAlpaca-Polyglot-12.8B"
        # model_path="nlpai-lab/kullm-polyglot-12.8b-v2"
        # model_path="beomi/llama-2-ko-7b"
        model_path="beomi/KoAlpaca-Polyglot-5.8B"  # 더 가벼운 모델
    )
    
    # 컴포넌트 초기화
    llm = LLMRunner(config)
    pm = PluginManager()
    agent = Agent(llm, pm)
    
    # 테스트 메시지 전송
    message = MCPMessage(
        role="user",
        type="text",
        content="안녕하세요, 오늘 날씨에 대해 알려주세요."
    )
    
    try:
        response = await agent.mcp_client.process(message)
        print("응답:", response.content)
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())