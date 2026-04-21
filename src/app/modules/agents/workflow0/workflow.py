import asyncio
from typing import Literal, TypeAlias

from langchain_core.messages import HumanMessage
from app.core.llm.factory import get_chat_model
from langgraph.graph import END, StateGraph, MessagesState

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from app.shared.nodes.thinking import create_model_node
from app.shared.routers.tool import tool_callback_router
from app.utils.prompt_loader import load_system_prompt, load_report_prompt
from app.shared.tools.retrieval import (
    fetch_external_data,
    rag_sammarize_tool,
)
from app.shared.tools.services import get_user_location, get_weather
from app.shared.tools.system import (
    fill_context_for_report,
    get_user_id,
    get_month_now,
)


tools = [
    rag_sammarize_tool,
    fetch_external_data,
    get_weather,
    get_user_location,
    get_user_id,
    get_month_now,
    fill_context_for_report,
]
tool_nodes = ToolNode(tools)
flow = StateGraph(MessagesState)
flow.add_node("tools", tool_nodes)
flow.add_node("call_model", create_model_node("call_model", load_system_prompt()))
flow.set_entry_point("call_model")
flow.add_conditional_edges(
    "call_model",
    tool_callback_router,      # 条件函数：返回 "tools" 或 "__end__"
    {
        "tools": "tools",      # 分支 key "tools" -> 节点 "tools"
        "__end__": END,        # 分支 key "__end__" -> 结束
    },
)
flow.add_edge("tools", "call_model")
checkpointer = MemorySaver()
app = flow.compile(checkpointer=checkpointer)


async def _run():
    first_state = await app.ainvoke(
        {"messages": [HumanMessage(content="这里天气如何？")]},
        config={"configurable": {"thread_id": "1"}},
    )
    result = first_state["messages"][-1].content
    print(result)

    second_state = await app.ainvoke(
        {"messages": [HumanMessage(content="我刚刚问了什么问题？")]},
        config={"configurable": {"thread_id": "1"}},
    )
    result = second_state["messages"][-1].content
    print(result)


if __name__ == "__main__":
    asyncio.run(_run())

    graph = app.get_graph()
    graph.draw_mermaid_png(output_file_path="workflow.png")