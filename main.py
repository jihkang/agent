import asyncio
from fastapi import FastAPI, WebSocket
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # 사용자의 요청 받기 (JSON 형태)
            data = await websocket.receive_text()
            user_request = json.loads(data)
            user_dict = {"content": user_request["content"]}

            # Router의 Generator 시작
            async for agent_messages in router.on_event(user_dict):
                for msg in agent_messages:
                    await websocket.send_text(json.dumps({
                        "sender": msg.sender,
                        "receiver": msg.receiver,
                        "payload": [p.dict() for p in msg.payload]
                    }))

                await asyncio.sleep(0.1)

       
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()


@app.get("/")
async def get_index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static", html=True), name="static")
