from collections.abc import AsyncGenerator
import json
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
            
            ** Output Rules **:
            1. If tool selected:
            - `content` follow tool's schema EXACTLY Empty field is accessible
            - Numbers must be string-wrapped (e.g., "37.5665" not 37.5665)
            2. If no tool:
            - `content` must be plain text explanation
            3. Reject if:
            - Missing required fields
            - Invalid data types/formats

            {mapped}
            if not supported content : string

            **Selection Criteria**:
            1. Match task requirements to tool capabilities with high confidence.
            2. Prefer specialized tools over general ones.
            3. Even if some required parameters are missing, prefer selecting the most appropriate tool and return missing parameters in the response.
            4. If no tool is appropriate, set "selected_tool" to empty string and explain why in "content".
            5. selected_tool "" or must in tools_list
            
            **Output Format** (STRICT JSON ONLY):
            {{
                "selected_tool": "exact_tool_name" | "",
                "content": "follow exact_tool_request" | "No suitable tool available"
            }}

            **Validation Examples**:
            Valid:
            {{
                "selected_tool": "WeatherToolAgent",
                "content": {{
                    "city": "Seoul",
                    "latitude": "37.549",
                    "longitude": "126.99",
                    "date": "20240506"
                }}
            }}

            Invalid (missing required):
            {{
                "selected_tool": "ReserveAgent",
                "content": {{"time": "14:00"}}  # Missing 'location'
            }}
            **IMPORTANT**: Return ONLY the JSON object as above. Do NOT include any explanations, markdown, or natural language text in your output. The "content" field must be a valid JSON object (not a string) if a tool is selected.
        """
        self.model = Model(local_dir)

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[List[AgentMessage]]:
        try:
            tools = self.plugin_manager.list_registry()
            
            tools_list = "\n".join([f'- "{tool}"' for tool in tools])
            tools_info = self.plugin_manager.pair_registry_execute_info()
            print(f"[Available Tools] {tools_info}")
            system_prompt = self.system_prompt_template.format(tools_list=tools_list, mapped="".join(tools_info))
            
            for payload in message.payload:
                content_data = payload.content
                # print(content_data)
                # if isinstance(content_data, list):
                #     queries = [item.content for item in content_data]
                # else:
                #     queries = [content_data.content]

                for query in content_data:
                    if not query.content:
                        response_message = MCPResponseMessage[str](content="ToolSelectorAgent: 실행할 작업이 없습니다.")
                        response_payload = MCPResponse[str](content=[response_message])
                        yield [AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload])]
                        continue
                    
                    request = query.content
                    if isinstance(request, dict):
                        send_query = ""
                        if "missing" in request:
                            append_query = "Fill this output"
                            append_query += json.dumps(request["missing"])
                            send_query += append_query

                        if "origin_task" in request:
                            send_query += json.dumps(request["origin_task"])

                        if send_query:
                            request = send_query
                    print("=========Tool Selector Query Result ==============")
                    print(query)

                    # 🔥 LLM 호출
                    llm_response = await self.model.ask(system_prompt, request)
                    print(llm_response)
                    print("===================================================")
                    # after local to change will be api then seperate code added.
                    if not llm_response:
                        raise e
                    

                    llm_response = llm_response if isinstance(llm_response, list) else [llm_response]
                    for response in llm_response:
                        if response.selected_tool == "":
                            raise "올바른 도구를 찾지못했습니다."

                         # ✅ original_task 가져오기 (없으면 query 전체가 original_task)
                        if isinstance(query, dict) and isinstance(response, dict):
                            original_task = query.get("original_task", query)
                            merged_content = {**original_task, **response.content}
                            # ✅ merge해서 content 갱신
                            response.content = merged_content
                        
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
            response_message = MCPResponseMessage[str](content="현재 해결을 위한 툴이 존재하지 않습니다.")
            response_payload = MCPResponse[str](content=[response_message], stop_reason="failure")
            yield [AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload])]
