import asyncio
from copy import deepcopy
import random
from typing import List
from fastapi import FastAPI, WebSocket
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse

from pydantic import BaseModel
import json
from plugin.manager import PluginManager
from router import Router
from scheme.a2a_message import AgentMessage
from fastapi.staticfiles import StaticFiles

app = FastAPI()

plugin_manager = PluginManager()
router = Router(plugin_manager)

class UserRequest(BaseModel):
    content: str

CACHED_DATA: List[str] = []
async def send_response(websocket: WebSocket, agent_message: AgentMessage):
    message = agent_message.payload
    for request in message:
        cached_response = request.model_dump()
        result = {
            f"{agent_message.sender}": cached_response
        }
        
        if cached_response in CACHED_DATA:
            return

        await websocket.send_text(json.dumps(result))
        await asyncio.sleep(0.3)

        CACHED_DATA.append(cached_response)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    id = 0
    while True:
        try:
            # 사용자의 요청 받기 (JSON 형태)
            CACHED_DATA = []
            data = await websocket.receive_text()
            user_request = json.loads(data)
            user_dict = {"content": user_request["content"], "metadata": {}}
            # Router의 Generator 시작
            async for agent_message in router.on_event(user_dict, str(id)):
                try:
                    # AgentMessage 객체를 직접 전달
                    await send_response(websocket, deepcopy(agent_message))
                except Exception as e:
                    print(f"send_response 또는 sleep 중 오류 발생: {e}")
                    # 한 메시지가 실패할 경우 클라이언트에 오류를 보내거나,
                    # 그냥 로그를 남기고 다음 메시지로 계속 진행하는 것을 고려
                    await websocket.send_text(json.dumps({"error": f"서버 메시지 처리 실패: {str(e)}"}))
                    continue
            
        except Exception as e:
            await websocket.send_text(json.dumps({"error": str(e)}))
            # await websocket.close()
        

        id += 1
        

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")


