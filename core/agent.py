from pydantic import BaseModel
from typing import Generic, List, Any
from core.plugin import PluginManager
from validator.validate import T

class AgentMessage(BaseModel):
    role: str
    content: str


class AgentResponse(BaseModel, Generic[T]):
    response: T


class Agent:
    history: List[AgentMessage]

    def __init__(self, llm: any, pm: PluginManager):
        self.llm = llm
        self.pm = pm
        self.history = []

    def run(self, problems: List[AgentMessage]) -> List[AgentResponse[Any]]:
        results = []

        # 입력 유효성 체크
        if not problems:
            return [AgentResponse(response={"error": "No input messages."})]

        messages = problems.copy()
        llm_reply = self.llm.run(messages)
        messages.append(llm_reply)

        # function_call 형식이면 plugin 실행
        if isinstance(llm_reply.content, dict) and "name" in llm_reply.content:
            function_name = llm_reply.content["name"]
            arguments = llm_reply.content.get("arguments", {})

            if self.pm.can_handle(function_name):
                plugin_result = self.pm.run(function_name, **arguments)
                messages.append(AgentMessage(role="function", content=plugin_result))

                final_reply = self.llm.run(messages)
                messages.append(final_reply)
                results.append(AgentResponse[str](response=final_reply.content))
            else:
                results.append(AgentResponse[str](response=f"Plugin '{function_name}'을 찾을 수 없습니다."))
        else:
            results.append(AgentResponse[str](response=llm_reply.content))

        self.history = messages
        return results

    def clear(self):
        self.history.clear()