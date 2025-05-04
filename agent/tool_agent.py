from collections.abc import AsyncGenerator
import os
from typing import List

from agent.selector.base import Agent
from models.model import Model
from plugin.manager import PluginManager
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage, MCPResponse, MCPResponseMessage
from utils.env import load_dotenv
from utils.logging import setup_logger

class ToolSelectorAgent(Agent):
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        
        load_dotenv()
        self.logger = setup_logger("tool_agent")
        local_model = os.getenv("LOCAL_MODEL")
        local_name = os.getenv("LOCAL_MODEL_NAME")
        local_dir = os.path.join(os.getenv("LOCAL_DIR"), local_model, local_name)
        self.model = Model(local_dir)

        self.system_prompt_template = """
        You are a ToolSelectorAgent. Your role is to choose the most appropriate tool (execution agent) to handle a given task.

        Available tools:
        {tools_list}

        Your job is to:
        1. Analyze the given task.
        2. Select the best tool (only one) that can perform the task most effectively.
        3. Extract the core instruction that should be executed.

        Return ONLY a JSON object in the following format:

        {{
            "selected_tool": "<tool_name>",
            "content": "<task_content_to_execute>"
        }}

        Only output the JSON. Do not include any explanations, reasoning, or additional text.
        """

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        try:
            tools = self.plugin_manager.list_registry()
            tools_list = "\n".join([f'- "{tool}"' for tool in tools])

            system_prompt = self.system_prompt_template.format(tools_list=tools_list)

            for payload in message.payload:
                content_data = payload.content
                if isinstance(content_data, list):
                    queries = [item.content for item in content_data]
                else:
                    queries = [content_data.content]

                result = []
                for query in queries:
                    if not query:
                        response_message = MCPResponseMessage[str](content="ToolSelectorAgent: 실행할 작업이 없습니다.")
                        response_payload = MCPResponse[str](content=[response_message])
                        result.append(AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload]))
                        continue

                    # 🔥 LLM 호출
                    llm_response = self.model.ask(system_prompt, query)
                    # after local to change will be api then seperate code added.
                    print(llm_response)
                    if not llm_response:
                        raise e
                    
                    new_msg = AgentMessage(
                        sender="ToolSelectorAgent",
                        receiver="ExecutionAgent",
                        payload=llm_response
                    )

                    result.append(new_msg)
                yield result

        except Exception as e:
            self.logger.error(f"ToolSelectorAgent 처리 중 시스템 오류 발생: {e}", exc_info=True)
            response_message = MCPResponseMessage[str](content="ToolSelectorAgent 시스템 오류 발생")
            response_payload = MCPResponse[str](content=[response_message], stop_reason="failure")
            yield [AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload])]
