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
    log: List[AgentMessage]

    def __init__(self, llm: any, pm: PluginManager):
        self.llm = llm
        self.pm = pm
        self.history = []
        self.log = []

    def _is_function_call(self, msg: AgentMessage) -> bool:
        return isinstance(msg.content, dict) and "name" in msg.content

    def run(self, problems: List[AgentMessage]) -> List[AgentResponse[Any]]:
        results = []

        # 입력 유효성 체크
        if not problems:
            return [AgentResponse(response={"error": "No input messages."})]

        max_steps = 5  # 무한 루프 방지를 위한 안전장치
        step = 0
        while step < max_steps:
            messages = problems.copy()
            
            llm_reply = self.llm.run(messages)
            self.log.append(llm_reply)
            self.history.append(llm_reply)
            
            if self._is_function_call(llm_reply):
                fn_name = llm_reply.content["name"]
                args = llm_reply.content.get("arguments", {})

                if not self.pm.can_handle(fn_name):
                    results.append(AgentResponse(response=f"Plugin '{fn_name}'은(는) 지원되지 않습니다."))
                    break

                plugin_result = self.pm.run(fn_name, **args)
                self.history.append(AgentMessage(role="function", content=plugin_result))
            else:
                results.append(AgentResponse(response=llm_reply.content))
                break  # 더 이상 function_call이 없으면 종료
            self.history = messages
            step += 1

        return results

    def clear(self):
        self.history.clear()