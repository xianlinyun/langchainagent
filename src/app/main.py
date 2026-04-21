from __future__ import annotations
from typing import Dict, Any
from contextlib import asynccontextmanager
import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.requests import Request
from pydantic import BaseModel, Field
from fastapi import Body

from fastapi import Request, HTTPException

from app.modules.agent.routers.api import router
from app.modules.rag.store.law_vector_store import VectorStoreService
from app.modules.rag.services.remote_embeddings import RemoteEmbeddingService
from app.modules.agents.contracts_explanation.workflow import build_contracts_explanation_app
from app.modules.agents.rag_searching.workflow import build_rag_search_app

# --- 1. 全局生命周期管理 ---
ml_models: dict[str, object] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("正在加载向量检索服务 (HTTP 模式)...")
    ml_models["agent"] = VectorStoreService()
    yield
    ml_models.clear()

app = FastAPI(title="法律助手 demo", version="0.1.0", lifespan=lifespan)


# --- 2. 基础对话接口 ---
@app.post("/chat")
async def chat(message: str):
    response = ml_models["agent"].answer(message)
    return {"reply": response}


# --- 3. 嵌入服务 (FastAPI 原生) ---
_embedding_service = RemoteEmbeddingService()


@app.post("/embed")
async def embed(text: str = Body(..., embed=True)):
    result = await _embedding_service.aembed_query(text)
    return JSONResponse(content={"embedding": result})


# --- 4. 配置与工作流 ---
_contracts_workflow_app = build_contracts_explanation_app()
_rag_search_workflow_app = build_rag_search_app()

class ContractsConfig(BaseModel):
    configurable: Dict[str, Any] | None = None

def _ensure_thread_id(request: Request, config: Dict[str, Any] = None) -> Dict[str, Any]:
    cfg = dict(config or {})
    configurable = cfg.setdefault("configurable", {})
    if any(k in configurable for k in ("thread_id", "checkpoint_id", "checkpoint_ns")):
        return cfg
    header_tid = request.headers.get("X-Thread-Id", None)
    configurable["thread_id"] = header_tid or "default-thread"
    return cfg

def sse_event_generator(workflow_app, input_data, config):
    # 返回标准 SSE 格式：每条消息以 data: ...\n\n
    async def event_stream():
        async for chunk in workflow_app.astream(input_data, config=config):
            if isinstance(chunk, dict):
                import json
                data = json.dumps(chunk, ensure_ascii=False)
            else:
                data = str(chunk)
            yield f"data: {data}\n\n"
    return event_stream


# --- 5. 路由注册（FastAPI 原生 SSE） ---

# 输入模型
class WorkflowInput(BaseModel):
    input: str
    config: Dict[str, Any] = None


@app.post("/contracts_explanation")
async def contracts_explanation(request: Request, body: WorkflowInput):
    if not body.input:
        raise HTTPException(status_code=422, detail="input 字段不能为空")
    config = _ensure_thread_id(request, body.config or {})
    input_data = {"input": body.input}
    event_stream = sse_event_generator(_contracts_workflow_app, input_data, config)
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/rag_search")
async def rag_search(request: Request, body: WorkflowInput):
    if not body.input:
        raise HTTPException(status_code=422, detail="input 字段不能为空")
    config = _ensure_thread_id(request, body.config or {})
    input_data = {"input": body.input}
    event_stream = sse_event_generator(_rag_search_workflow_app, input_data, config)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

app.include_router(router)

if __name__ == "__main__":
    # 彻底放弃证书：不要在这里添加 ssl_keyfile 或 ssl_certfile
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)