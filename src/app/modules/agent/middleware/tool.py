from typing import Callable, Awaitable

from app.utils.logger_handler import get_logger
from langchain.agents.middleware import AgentMiddleware, ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

logger = get_logger(__name__)


class MonitorTool(AgentMiddleware):
    """同时支持同步和异步调用的工具监控中间件。"""

    # 同步工具调用（用于 agent.stream / invoke）
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        logger.info(f"[tool monitor]执行工具:{request.tool_call['name']}")
        logger.info(f"[tool monitor]传入参数:{request.tool_call['args']}")
        try:
            response = handler(request)
            logger.info(f"[tool monitor]工具:{request.tool_call['name']}调用成功")
            if request.tool_call["name"] == "fill_context_for_report":
                request.runtime.context["report"] = True
            return response
        except Exception as e:
            logger.error(f"工具{request.tool_call['name']}调用失败,因为:{str(e)}")
            raise e

    # 异步工具调用（用于 agent.astream / ainvoke）
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
    ) -> ToolMessage | Command:
        logger.info(f"[tool monitor]执行工具:{request.tool_call['name']}")
        logger.info(f"[tool monitor]传入参数:{request.tool_call['args']}")
        try:
            response = await handler(request)
            logger.info(f"[tool monitor]工具:{request.tool_call['name']}调用成功")
            if request.tool_call["name"] == "fill_context_for_report":
                request.runtime.context["report"] = True
            return response
        except Exception as e:
            logger.error(f"工具{request.tool_call['name']}调用失败,因为:{str(e)}")
            raise e
