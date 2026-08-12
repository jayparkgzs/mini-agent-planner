# main.py
import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from scheduler.pipeline import pipeline
from agent.core import ReActAgent
from scheduler.pipeline import pipeline

load_dotenv()

app = FastAPI(title="Mini Agent Planner", version="2.0")

agent = ReActAgent(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model=os.getenv("MODEL_NAME", "gpt-3.5-turbo")
)


# ============ 原有接口 ============

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
        "message": "Mini Agent Planner v2.0 已启动",
        "endpoints": {
            "chat": "POST /chat",
            "confirm": "POST /confirm",
            "history": "GET /history",
            "review": "POST /review - 代码审查流水线",
            "review_agents": "GET /review/agents"
        }
    }


# ============ 新增：代码审查流水线接口 ============

class ReviewRequest(BaseModel):
    code: str
    filename: str = "main.py"
    pr_id: str = "PR-001"


@app.post("/review")
async def code_review(request: ReviewRequest):
    """
    自动化代码审查流水线
    并行执行安全、性能、规范三个子 Agent
    """
    try:
        report = await pipeline.run(
            code=request.code,
            filename=request.filename,
            pr_id=request.pr_id
        )
        
        return {
            "pr_id": report.pr_id,
            "overall_score": report.overall_score,
            "status": report.status,
            "duration_ms": round(report.duration_ms, 2),
            "reviews": report.reviews,
            "markdown_report": report.summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/review/agents")
async def list_review_agents():
    """列出代码审查流水线中的子 Agent"""
    return {
        "agents": [
            {"name": "security", "description": "安全审查（漏洞、密钥泄露、注入）"},
            {"name": "performance", "description": "性能审查（N+1查询、循环优化）"},
            {"name": "style", "description": "规范审查（命名、缩进、文档）"}
        ]
    }


# ============ 新增：观测与诊断接口 ============

from observability.tracer import tracer
from observability.debugger import AgentDebugger

debugger = AgentDebugger()


@app.get("/traces")
async def get_traces():
    """获取所有追踪记录"""
    return {
        "total": len(tracer.traces),
        "traces": tracer.traces[-10:]  # 最近10条
    }


@app.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    """获取指定追踪详情"""
    for t in tracer.traces:
        if t["trace_id"] == trace_id:
            return t
    raise HTTPException(status_code=404, detail="Trace not found")


@app.post("/diagnose")
async def diagnose():
    """
    诊断最近一次失败
    """
    failures = tracer.get_failure_traces()
    if not failures:
        return {"status": "ok", "message": "最近没有失败记录"}
    
    last_failure = failures[-1]
    diagnosis = debugger.analyze(last_failure)
    return diagnosis


@app.get("/diagnose/report")
async def diagnosis_report():
    """
    生成失败模式统计报告
    """
    analysis = debugger.analyze_all_failures(tracer.traces)
    return {
        "report": analysis,
        "total_traces": len(tracer.traces),
        "failure_rate": len(tracer.get_failure_traces()) / len(tracer.traces) if tracer.traces else 0
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
