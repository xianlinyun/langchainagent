from langgraph.graph import END, StateGraph, MessagesState

from typing import Literal, TypeAlias
from app.shared.nodes.thinking import create_model_node


async def call_model(state: MessagesState):
    # 调用共享的基础方法，但传入私有的 Prompt 和配置
    return await create_model_node(
        
    )