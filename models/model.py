from typing import Any, List
import aiohttp
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest
from llama_cpp import Llama
from utils.util import convert_to_agent_message_api, convert_to_agent_message_local

# now use tiny model but when evaluating this systems then use large model 
# to use image -etc..
class Model:
    def __init__(self, model = "", prompt = ""):
        self.model = Llama(model_path=model, n_ctx=2048, n_threads=8, prompt=prompt)
    
    async def ask(self, prompt: str = "", request: str = "", convert_need: bool = True) -> List[MCPRequest[Any]] | List[str]:
        full_prompt = f"""[INST] <<SYS>>
            {prompt}
            <</SYS>>

            {request}
            [/INST]
        """

        response = self.model(
            full_prompt,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.95,
            repeat_penalty=1.1,
            stop=["</s>", "[INST]"]
        )
        
        response = [ret["text"].rstrip() for ret in response["choices"]]
        if convert_need: 
            return convert_to_agent_message_local(response)
        
        return response
    

class ApiModel:
    def __init__(self, provider: str="gemini", api_key: str="", model_name: str=""): 
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
    
    async def ask(self, prompt:str, request: str = "", request_sender="") -> List[AgentMessage]:
        headers = {
            "Content-Type": "application/json",
        }
        params = {
            "key": self.api_key
        }
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{prompt}\n\n{request}"}]}
            ]
        }

        res_json = {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, params=params, json=body) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise Exception(f"GeminiLite API 호출 실패: {resp.status} {text}")
                    res_json = await resp.json()
                    candidates = res_json["candidates"]
                    content = []
                    for candidate in candidates:
                        parts = candidate.get("content", {}).get("parts", [])
                        for part in parts:
                            if "text" in part:
                                content.append(part["text"])
                    if not all(isinstance(x, str) for x in content):
                        raise ValueError("응답 content에 문자열이 아닌 요소가 포함되어 있음")
                    
                    return convert_to_agent_message_api(request_sender, content)

        except Exception as e:
            raise Exception(f"GeminiLite 응답 파싱 실패: {e}\n응답내용: {res_json}")