"""
不要让 LLM 决定什么时候去获取 ID，最好直接“喂”给它。

在 FastAPI 路由中，你通常已经通过 Depends(get_current_user) 拿到了用户信息。与其让 Agent 浪费 Token 去调工具问“我是谁？”，不如在初始化 Agent 时，直接把 user_id 注入到 Prompt 的 System Message 中：

"你是一个扫地机助手。当前对话的用户 ID 是 USR_12345。在调用涉及订单或隐私的工具时，请使用此 ID。"

这样处理不仅能节省 Token，还能避免 Agent 因为获取 ID 失败而导致的逻辑中断。
"""

from langchain_core.tools import tool


@tool(description="这是一个获取系统id的工具。输入为空，输出是系统的基本信息。")
def get_user_id() -> str:
    """
    这是一个获取系统id的工具。输入为空，输出是系统的基本信息。
    :return: 系统的基本信息
    """
    return "1004"


@tool(description="这是一个获取当前月份的工具。输入为空，输出是当前月份。")
def get_month_now() -> str:
    """
    这是一个获取当前月份的工具。输入为空，输出是当前月份。
    :return: 当前月份
    """

    return "2025-03"


@tool(
    description="这是一个填充上下文的工具。输入为空，输出是一个包含系统基本信息的字符串。"
)
def fill_context_for_report():
    """
    这是一个填充上下文的工具。输入为空，输出是一个包含系统基本信息的字符串。
    :return: 包含系统基本信息的字符串
    """
    return "fill_context_for_report已调用"
