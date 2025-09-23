from typing import Any, List
import aiohttp
from models.api_model import ApiRequest, ApiResponse, Content, ContentPart, Params
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest
from llama_cpp import Llama
from utils.constant import END_POINTS, SYSTEM_PROMPT
from utils.util import convert_to_agent_message_api, convert_to_agent_message_local

# now use tiny model but when evaluating this systems then use large model 
# to use image -etc..
class Model:
    def __init__(self, model = "", prompt = ""):
        self.model = Llama(model_path=model, n_ctx=2048, n_threads=8, prompt=prompt)
    
    def build_prompt(self, system_prompt: str, user_request: str) -> str:    
        """SYSTEM_PROMPT의 플레이스홀더를 채워 완성된 프롬프트를 반환합니다."""
        return SYSTEM_PROMPT.format(
            replace_system_prompt=system_prompt,
            replace_user_request=user_request,
        )

    async def ask(self, prompt: str = "", request: str = "") -> List[MCPRequest[Any]]:
        """ send default system_prompt and user request to local model and get response"""
        response = self.model(
            self.build_prompt(prompt, request),
            max_tokens=1024,
            temperature=0.7,
            top_p=0.95,
            repeat_penalty=1.1,
            stop=["</s>", "[INST]"]
        )

        # response 의 choice로 반환된 데이터중 텍스트만 추출해서 합쳐서 문자열로 변환
        response = [ret["text"].rstrip() for ret in response["choices"]]
        return convert_to_agent_message_local(response)
    

class ApiModel:
    def __init__(self, provider: str="gemini", api_key: str="", model_name: str=""): 
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = END_POINTS[provider].format(replace_model_name=model_name)

    async def ask(self, prompt:str, request: str = "", request_sender="") -> List[AgentMessage]:
        """ send default system_prompt and user request to api model and get response"""

        try:
            req = ApiRequest(
                params=Params(key=self.api_key),
                contents=[
                    Content(role="user", parts=[ContentPart(text=f"{prompt}\n\n{request}")])
                ]
            )
            res_json = {}
            async with aiohttp.ClientSession() as session:
                http_args = req.to_http()
                async with session.post(self.endpoint, **http_args) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise Exception(f"GeminiLite API 호출 실패: {resp.status} {text}")
                    res_json = await resp.json()
                    parsed_json = ApiResponse.from_json(res_json)
                    if not all(isinstance(x, str) for x in parsed_json.texts):
                        raise ValueError("응답 content에 문자열이 아닌 요소가 포함되어 있음")
                    return convert_to_agent_message_api(request_sender, parsed_json.texts)

        except Exception as e:
            raise Exception(f"GeminiLite 응답 파싱 실패: {e}\n응답내용: {res_json}")