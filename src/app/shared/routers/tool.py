from langgraph.graph import END, StateGraph, MessagesState

from typing import TypeAlias,Literal

from typing import Literal, Callable, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import END

def tool_callback_router(
    state: Any, 
    tool_node_name: str = "tools", 
    end_node_name: str = END
) -> str:
    """
    通用工具回调路由
    :param state: 只要 state 中包含 messages 即可
    :param tool_node_name: 存在工具调用时跳转的节点名
    :param end_node_name: 结束时跳转的节点名 (默认 END)
    """
    # 兼容 MessagesState 或自定义 Dict State
    messages = state.get("messages", []) if isinstance(state, dict) else state.messages
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return tool_node_name
    return end_node_name