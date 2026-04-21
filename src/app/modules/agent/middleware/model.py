from typing import Callable
from app.utils.logger_handler import get_logger
from langchain.agents.middleware import (
    AgentState,
    wrap_tool_call,
    ToolCallRequest,
    before_model,
)
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.runtime import Runtime

logger = get_logger(__name__)


@before_model
def log_before_model(state: AgentState, runtime: Runtime):
    logger.info(f"[log_before_model]即将调用模型,带有 {len(state['messages'])} 条消息")
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__}: 新增消息内容: {state['messages'][-1].content}")
    return state
    
