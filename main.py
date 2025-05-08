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
    # AgentMessage → MCPResponse → MCPResponseMessage → content
    response_payload = agent_message.payload[0]  # MCPResponse[Any]
    response_message = response_payload.content[0]  # MCPResponseMessage[Any]

    cached_response = response_message.json()
    if cached_response in CACHED_DATA:
        return 
    
    await websocket.send_text(cached_response)
    CACHED_DATA.append(cached_response)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    id = 0
    while True:
        try:
            # 사용자의 요청 받기 (JSON 형태)
            data = await websocket.receive_text()
            user_request = json.loads(data)
            user_dict = {"content": user_request["content"]}
            # Router의 Generator 시작
            async for agent_messages in router.on_event(user_dict, str(id)):
                print("[AgentMessage]=================")
                print(agent_messages)
                print("===============================")
                for agent_message in agent_messages:
                    try:
                        await send_response(websocket, deepcopy(agent_message))
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(e)
                        continue 

            CACHED_DATA = []
        except Exception as e:
            await websocket.send_text(json.dumps({"error": str(e)}))
        # await websocket.close()
        id += 1

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static", html=True), name="static")
