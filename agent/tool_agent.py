from collections.abc import AsyncGenerator
import os
from typing import List

from agent.selector.base import Agent
from models.model import Model
from plugin.manager import PluginManager
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPResponse, MCPResponseMessage
from utils.env import load_dotenv
from utils.logging import setup_logger

class ToolSelectorAgent(Agent):
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        
        load_dotenv()
        self.logger = setup_logger("toolAgent")
        local_model = os.getenv("LOCAL_MODEL")
        local_name = os.getenv("LOCAL_MODEL_NAME")
        local_dir = os.path.join(os.getenv("LOCAL_DIR"), local_model, local_name)
        self.system_prompt_template = """
            **Available Tools** (Must use EXACT names):
            {tools_list}
            """
        self.system_prompt_for_execution = """    
            **Selection Criteria**:
            1. Match task requirements to tool capabilities with high confidence.
            2. Prefer specialized tools over general ones.
            3. Only select a tool if all required parameters can be extracted from the task.
            4. If no tool is appropriate, set "selected_tool" to empty string and explain why in "content".
            5. selected_tool "" or must in tools_list
            **Output Format** (STRICT JSON ONLY):
            {{
                "selected_tool": "exact_tool_name" | "",
                "content": {tool_select_info}
            }}

            **Examples**:

            Input: "Find current weather in Seoul"
            Output: {{
                "selected_tool": "weather_api",
                "content": {{
                    "content": "get_current_weather",
                    "parameters": {{"city": "Seoul"}}
                }}
            }}

            Input: "Book flight to Paris"
            Output: {{
                "selected_tool": "",
                "content": "No booking tool available"
            }}

            **IMPORTANT**: Return ONLY the JSON object as above. Do NOT include any explanations, markdown, or natural language text in your output. The "content" field must be a valid JSON object (not a string) if a tool is selected.
        """
        self.model = Model(local_dir)

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        try:
            tools = self.plugin_manager.list_registry()
            print(tools)
            tools_list = "\n".join([f'- "{tool}"' for tool in tools])
            system_prompt = self.system_prompt_template.format(tools_list=tools_list)
            for payload in message.payload:
                content_data = payload.content
                if isinstance(content_data, list):
                    queries = [item.content for item in content_data]
                else:
                    queries = [content_data.content]

                for query in queries:
                    if not query:
                        response_message = MCPResponseMessage[str](content="ToolSelectorAgent: 실행할 작업이 없습니다.")
                        response_payload = MCPResponse[str](content=[response_message])
                        yield [AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload])]
                        continue
                    
                    # 🔥 LLM 호출
                    llm_response = await self.model.ask(system_prompt, query)

                    # after local to change will be api then seperate code added.
                    if not llm_response:
                        raise e

                    llm_response if isinstance(llm_response, list) else [llm_response]
                    for response in llm_response:
                        if response.selected_tool == "":
                            raise "올바른 도구를 찾지못했습니다."
                        
                        new_msg = AgentMessage(
                            id = message.id,
                            sender="ToolSelectorAgent",
                            receiver="ExecutionAgent",
                            payload=[response]
                        )
                        
                        self.logger.info(new_msg)
                        yield new_msg

        except Exception as e:
            self.logger.error(f"ToolSelectorAgent 처리 중 시스템 오류 발생: {e}", exc_info=True)
            response_message = MCPResponseMessage[str](content="ToolSelectorAgent 시스템 오류 발생")
            response_payload = MCPResponse[str](content=[response_message], stop_reason="failure")
            yield [AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload])]
