from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.modules.agent.services.react_agent import ReactAgent


class AgentRequestDTO(BaseModel):
    query: str


router = APIRouter(prefix="/agent", tags=["agent"])

# 复用同一个 Agent 实例，避免每次请求都重新加载模型
agent = ReactAgent(config={})


@router.post("/chat/stream")
async def agent_stream_endpoint(request: AgentRequestDTO):
    """流式返回 ReactAgent 的输出。

    返回纯文本流，前端可以按行/按块读取；
    若需要 SSE，可将 media_type 改为 "text/event-stream" 并按 SSE 格式拼接。
    """

    def event_generator():
        for chunk in agent.execute_stream(request.query):
            # 这里直接透传，每个 chunk 末尾已有换行符
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")