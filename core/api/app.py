
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from core.agent import Agent
from core.mcp import MCPResult, MCPMessage
from core.validator.validate import isValid

#init api server
app = FastAPI()


#api listening
@app.post("/ask", response_model = MCPResult)
def askMCP(message: MCPMessage):
    isValid(message)
    mcpMsg = MCPMessage(message)