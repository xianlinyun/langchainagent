from typing import Any, Callable, Optional, List
from langchain_core.messages import SystemMessage, BaseMessage
from app.core.config import Settings
from app.core.llm.factory import get_chat_model

def create_model_node(
    node_name: str,
    system_prompt: str,
    temperature: float = Settings.agent.temperature,
    tools: Optional[List[Any]] = None,
    message_save_num: int = Settings.agent.message_save_num,
) -> Callable:
    """
    Agent 节点工厂：生成一个标准的异步 LLM 调用节点
    """
    # 预加载模型，支持绑定工具
    model = get_chat_model(temperature=temperature)
    if tools:
        model = model.bind_tools(tools)

    async def _node(state: Any) -> dict:
        # 1. 自动适配不同的 State 类型 (MessagesState 或 自定义 Dict)
        if isinstance(state, dict):
            messages = state.get("messages", [])[-message_save_num:]  # 取最后几条消息作为输入
        else:
            messages = state.messages[-message_save_num:]

        # 2. 注入 System Prompt
        full_messages = [SystemMessage(content=system_prompt)] + messages
        
        # 3. 异步调用 (高手用 ainvoke)
        # 可以在这里统一加重试逻辑 (retry) 或 监控埋点
        response = await model.ainvoke(full_messages)
        
        # 4. 返回标准格式，并在 metadata 中标记来源
        return {
            "messages": [response],
            "sender": node_name
        }

    return _node