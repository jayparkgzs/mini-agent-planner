# main.py
import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.core import ReActAgent

load_dotenv()

app = FastAPI(title="Mini Agent Planner", version="1.0")

agent = ReActAgent(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model=os.getenv("MODEL_NAME", "gpt-3.5-turbo")
)


class ChatRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    confirm: bool


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(agent.run, request.message),
            timeout=60.0
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="LLM 响应超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/confirm")
async def confirm(request: ConfirmRequest):
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(agent.confirm, request.confirm),
            timeout=30.0
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history():
    return {"history": agent.history}


@app.get("/")
async def root():
    return {
        "message": "Mini Agent Planner 已启动",
        "usage": {
            "chat": "POST /chat",
            "confirm": "POST /confirm",
            "history": "GET /history"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
