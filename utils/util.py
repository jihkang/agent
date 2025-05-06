import json
from pathlib import Path
import subprocess
import sys
import importlib
from typing import Any, List
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage, MCPResponse, MCPResponseMessage
from utils.logging import setup_logger


# 패키지 이름과 실제 import 이름이 다를 때를 위한 매핑
PACKAGE_MAP = {
    "python-dotenv": "dotenv",
}

def safe_import(package: str, import_as: str = None):
    """
    pip 패키지를 안전하게 설치하고 import합니다.
    
    Args:
        package (str): pip install 할 패키지 이름 (예: "python-dotenv")
        import_as (str): 실제 import 할 이름 (예: "dotenv"). 생략 시 자동 매핑 or 동일 처리.

    Returns:
        module: import된 모듈 객체
    """
    module_name = import_as or PACKAGE_MAP.get(package, package)

    try:
        return importlib.import_module(module_name)
    except ImportError:
        print(f"[safe_import] '{module_name}' 모듈이 없어 설치 중... ⏳")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"[safe_import] '{package}' 설치 완료 ✅")
        return importlib.import_module(module_name)
    

def check_file(path: str, filename: str = "") -> bool:
    path = Path(path)
    if filename == "":
        return path.exists()
    return any(path.rglob(filename))


def convert_to_agent_message_local(response_text: List[str]) -> List[MCPRequest]:
    logger = setup_logger("DefaultModel")
    messages = []

    try:
        for response in response_text:
            if response.startswith("```json"):
                response = response.lstrip("```json").rstrip("```").strip()
            elif response.startswith("```"):
                response = response.lstrip("```").rstrip("```").strip()
        
            parsed_response = json.loads(response)
            print(parsed_response)

            selected_tool = parsed_response.get("selected_tool", "")
            task_content = parsed_response.get("content")

            # MCPRequestMessage 생성
            payload_obj = MCPRequest[type(task_content)](content=[MCPRequestMessage[type(task_content)](content=task_content)], selected_tool=selected_tool, dag=-1)
            messages.append(payload_obj)

    except json.JSONDecodeError as e:
        logger.error(f"[convert_tool_selection_message] JSON 파싱 에러: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[convert_tool_selection_message] 알 수 없는 에러: {e}", exc_info=True)
    
    return messages

def convert_to_agent_message_api(request_sender: str, response_text: List[str]) -> List[AgentMessage]:
    agent_messages = []

    try:
        for response in response_text:
            if response.startswith("```json"):
                response = response.lstrip("```json").rstrip("```").strip()
            elif response.startswith("```"):
                response = response.lstrip("```").rstrip("```").strip()

            parsed_response = json.loads(response)

            for item in parsed_response:
                sender = request_sender
                receiver = item.get("receiver")
                payload_data = item.get("payload", [])
                payload_objs = []
                id = item.get("id")
                for data in payload_data:
                    if isinstance(data, dict):
                        if receiver == "user":
                            payload_objs.append(
                                MCPResponse(content=[MCPResponseMessage(**data)])
                            )
                        else:
                            payload_objs.append(
                                MCPRequest(content=[MCPRequestMessage(**data)])
                            )

                agent_message = AgentMessage(
                    id = id,
                    sender=sender,
                    receiver=receiver,
                    payload=payload_objs
                )

                agent_messages.append(agent_message)

    except json.JSONDecodeError as e:
        print(f"[convert_to_agent_message] JSON 파싱 에러: {e}")
    except Exception as e:
        print(f"[convert_to_agent_message] 알 수 없는 에러: {e}")

    return agent_messages


def add_request(data: AgentMessage) -> bool:
    for payload in data.payload:
        if isinstance(payload, MCPResponse):
            result =  getattr(payload, "stop_reason", "")
            if result is "done" or result is "failure": 
                return False

    return True