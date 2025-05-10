from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import importlib
from typing import Any, List, Union
from scheme.a2a_message import AgentMessage
from scheme.mcp import MCPRequest, MCPRequestMessage
from utils.constant import SUCCESS
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


def fix_json_keys(response_text: str) -> str:
    # 따옴표 없는 키를 쌍따옴표로 감싸줌
    fixed = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', response_text)
    return fixed

def convert_to_agent_message_local(response_text: List[str]) -> List[MCPRequest]:
    logger = setup_logger("DefaultModel")
    messages = []

    try:
        for response in response_text:
            if response.startswith("```json"):
                response = response.lstrip("```json").rstrip("```").strip()
            elif response.startswith("```"):
                response = response.lstrip("```").rstrip("```").strip()
            response = fix_json_keys(response)
            parsed_response = json.loads(response)

            selected_tool = parsed_response.get("selected_tool", "")
            task_content = parsed_response.get("content")
            metadata = parsed_response.get("metadata")
            payload_obj = MCPRequest(
                content=[
                    MCPRequestMessage(content=task_content, metadata=metadata)
                ],
                selected_tool=selected_tool,
            )
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
            response = fix_json_keys(response)
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
                                MCPRequest(content=[MCPRequestMessage(**data)])
                            )
                        else:
                            payload_objs.append(
                                MCPRequest(content=[MCPRequestMessage(**data)])
                            )
                
                agent_message = AgentMessage(
                    id = id,
                    sender=sender,
                    receiver=receiver,
                    payload=payload_objs,
                    dag=item.get("dag", id),
                    origin_request="",
                    stop_reason=SUCCESS
                )

                agent_messages.append(agent_message)

    except json.JSONDecodeError as e:
        print(f"[convert_to_agent_message] JSON 파싱 에러: {e}")
    except Exception as e:
        print(f"[convert_to_agent_message] 알 수 없는 에러: {e}")

    return agent_messages

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

def get_description_from_class_path(cls_path: str) -> dict | None:
    """
    cls_path를 받아서 동일 경로의 md(플러그인의 설명)파일을 읽어온다.
    없으면 None 반환
    """
    # 1. 'plugins.my_plugin.MyPlugin' -> 'plugins/my_plugin.json' 변환
    path_parts = cls_path.split(".")
    dir_path = os.path.join(*path_parts[:-1])  # 파일명 제외
    description_path = f"{dir_path}.md"

    # 2. 파일 존재 여부 확인 없으면 어떤 응답이던 상관없음.
    if not os.path.exists(description_path):
        return ""

    # 3. 파일 읽기
    with open(description_path, "r", encoding="utf-8") as f:
        description = f.read()

    return description


def merge_metadata_only(prev: AgentMessage, current: AgentMessage) -> AgentMessage:
    new_msg = deepcopy(current)
    
    prev_metadata = getattr(prev.payload[0].content[0], "metadata", {}) or {}
    curr_message = new_msg.payload[0].content[0]

    # metadata 병합 (current 우선)
    merged_metadata = {**prev_metadata, **curr_message.metadata}
    curr_message.metadata = merged_metadata
    
    return new_msg

def flatten_agent_messages(data: Union[AgentMessage, List[AgentMessage], List[List[AgentMessage]]]) -> List[AgentMessage]:
    """AgentMessage 또는 중첩된 리스트를 평탄화하여 List[AgentMessage]로 반환"""
    if isinstance(data, AgentMessage):
        return [data]
    elif isinstance(data, list):
        result = []
        for item in data:
            result.extend(flatten_agent_messages(item))
        return result
    else:
        raise TypeError(f"[flatten_agent_messages] Invalid type: {type(data)}")