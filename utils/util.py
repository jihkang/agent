from copy import deepcopy
import json
import os
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

def get_schema_from_class_path(cls_path: str) -> dict | None:
    """
    cls_path를 받아서 동일 경로의 json 파일을 읽어온다.
    없으면 None 반환
    """
    # 1. 'plugins.my_plugin.MyPlugin' -> 'plugins/my_plugin.json' 변환
    path_parts = cls_path.split(".")
    dir_path = os.path.join(*path_parts[:-1])  # 파일명 제외
    json_path = f"{dir_path}.json"

    # 2. 파일 존재 여부 확인 없으면 어떤 응답이던 상관없음.
    if not os.path.exists(json_path):
        return ""

    # 3. 파일 읽기
    with open(json_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    return schema

def merge_agent_messages(previous_messages: List[AgentMessage], new_message: AgentMessage) -> AgentMessage:
    """이전 AgentMessage 리스트와 새로운 AgentMessage를 병합."""
   
def merge_agent_messages(previous_messages: List[AgentMessage], new_message: AgentMessage) -> AgentMessage:
    """이전 AgentMessage 리스트와 새로운 AgentMessage를 병합."""

    if not previous_messages:
        return deepcopy(new_message)  # 그냥 새 메시지를 반환

    # 새로운 메시지 복사 (deepcopy 필수!)
    merged_message = deepcopy(new_message)

    # content를 병합할 dict 생성
    merged_content = {}

    for previous in previous_messages:
        for prev_payload in previous.payload:
            for prev_content in prev_payload.content:
                if hasattr(prev_content, "content"):
                    for k, v in prev_content.content.items():
                        merged_content[k] = v  # 이전 값 저장

    # 이제 new_message 의 content를 덮어씌움
    for new_payload in merged_message.payload:
        for new_content in new_payload.content:
            if hasattr(new_content, "content"):
                for k, v in new_content.content.items():
                    merged_content[k] = v  # 새로운 값으로 overwrite

        # content는 **무조건 하나짜리 리스트**로 유지
        new_payload.content = [MCPRequestMessage(content=merged_content)]

    return merged_message