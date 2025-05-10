from collections.abc import AsyncGenerator
from copy import deepcopy
import json
import os
from typing import List
from agent.selector.base import Agent
from models.model import Model
from plugin.manager import PluginManager
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import FAIL, SUCCESS
from utils.env import load_dotenv
from utils.logging import setup_logger
from utils.util import merge_metadata_only

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
if not supported content : string, metadata: {{}}

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
    "metadata": {{
        "to use this tool parameter if empty then just {{}}
    }}
}}

**Validation Examples**:
Valid:
{{
    "selected_tool": "WeatherToolAgent",
    "content": "give me Seoul Weather",
    "metadata": {{
        "city": "Seoul",
        "latitude": "37.549",
        "longitude": "126.99",
        "date": "20240506"
    }}
}}


**IMPORTANT**: Return ONLY the JSON object as above. Do NOT include any explanations, markdown, or natural language text in your output.

Return a SINGLE JSON object.
Selected_tool must be set selected_tool = selected_tool_name
Do NOT put the entire response inside the metadata field.
The metadata field is only for parameters, not full structure.

The "content" field must be previous request
The "metadata" field must be a valid JSON object (not a string) if a tool is selected.
        """
        self.model = Model(local_dir)

    async def on_event(self, message: AgentMessage) -> AsyncGenerator[AgentMessage]:
        try:        
            tools = self.plugin_manager.list_registry()
            
            tools_list = "\n".join([f'- "{tool}"' for tool in tools])
            
            tools_info = self.plugin_manager.pair_registry_execute_info()
            system_prompt =  self.system_prompt_template.format(tools_list=tools_list, mapped="".join(tools_info))
            print(system_prompt)
            
            for payload in message.payload:
                content_data = payload.content
                
                if not isinstance(content_data, list):
                    content_data = [content_data]

                for query in content_data:
                    if not query.content:
                        response_message = MCPRequestMessage[str](content="ToolSelectorAgent: 실행할 작업이 없습니다.")
                        response_payload = MCPRequest[str](content=[response_message])
                        yield AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload], id=message.id, dag=message.dag)
                        continue
                    
                    request = query.content 

                    metadata = deepcopy(query.metadata)
                    if isinstance(metadata, list):
                        metadata = " ".join([str(item) for item in metadata])
                    elif isinstance(metadata, dict):
                        if len(metadata.keys()) > 0:
                            if metadata.get("content"):
                                del metadata["content"]

                            metadata = json.dumps(metadata, ensure_ascii=False)
                            
                    elif not isinstance(metadata, str):
                        metadata = str(metadata)
                    
                    if isinstance(metadata, str):
                        request += f"\n\nAdditional context (metadata):\n{metadata}"

                    print("=========Tool Selector Query Result ==============")
                    print(request)
                    # 🔥 LLM 호출
                    final_response = []
                    for _ in range(3):
                        llm_response = await self.model.ask(system_prompt, request)
                        
                        if len(llm_response) > 0:
                            final_response.extend(llm_response)
                            break
                    
                    print(llm_response)
                    
                    print("===================================================")
                    # after local to change will be api then seperate code added.
                    if not llm_response or len(llm_response) == 0:
                        raise ValueError(f"{request}를 해결할 올바른 도구를 찾지못했습니다.")
                    
                    for response in llm_response:
                        if response.selected_tool == "":
                            raise ValueError(f"{request}를 해결할 올바른 도구를 찾지못했습니다.")
 
                        new_msg = AgentMessage(
                            id = message.id,
                            dag = message.dag,
                            sender="ToolSelectorAgent",
                            receiver="ExecutionAgent",
                            payload=[response],
                            stop_reason=SUCCESS
                        )
                        new_msg = merge_metadata_only(message, new_msg)
                        self.logger.info(new_msg)
                        yield new_msg

        except ValueError as v: 
            self.logger.error(f"ToolSelectorAgent {v}", exc_info=True)
            response_message = MCPRequestMessage[dict](content=str(v), metadata = {})
            response_payload = MCPRequest[dict](content=[response_message], stop_reason=FAIL)
            yield AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload], id=message.id, dag=message.dag, stop_reason=FAIL)

        except Exception as e:
            self.logger.error(f"ToolSelectorAgent 처리 중 시스템 오류 발생: {e}", exc_info=True)
            response_message = MCPRequestMessage[dict](content=str(e), metadata = {})
            response_payload = MCPRequest[dict](content=[response_message], stop_reason=FAIL)
            yield AgentMessage(sender="ToolSelectorAgent", receiver="user", payload=[response_payload], id=message.id, dag=message.dag, stop_reason=FAIL)
