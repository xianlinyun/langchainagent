import asyncio

from langgraph.graph import END, START, StateGraph
import operator
from typing import Annotated, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from app.modules.agents.rag_searching.node import (
    check_node,
    extract_node,
    clarification_node,
    category_node,
    output_node,
    retriver_node,
    generator_node,
)


class StatePlanExecute(TypedDict, total=False):
    """工作流状态定义。

    通过 total=False 将除需要的字段外都设为可选，
    这样通过 LangServe 只传 {"input": {"input": "..."}} 也能通过校验。
    其他字段在节点内部按需补充。
    """

    # 用户当前输入（必需字段，调用方传入）
    input: str
    # 以下字段均由工作流内部维护，调用方可以不传
    plan: list[str]
    past_steps: Annotated[list[tuple], operator.add]
    response: str
    contract_info: dict
    rag_docs: list[str]


def build_rag_search_app():
    """构建并返回 RAG 搜索工作流的 LangGraph 应用，用于 LangServe/业务调用。"""

    workflow = StateGraph(StatePlanExecute)

    workflow.add_node("input", extract_node)
    workflow.add_node("add", clarification_node)
    workflow.add_node("category", category_node)
    workflow.add_node("RAG", retriver_node)
    workflow.add_node("write", generator_node)
    workflow.add_node("check", check_node)
    workflow.add_node("output", output_node)

    # 定义从检查节点到下一步的条件路由：
    # - 若检查通过（check_result["is_pass"] 为 True），则进入输出节点结束流程；
    # - 若检查不通过，则在写作节点之间有限次打回重写，避免死循环。
    def route_check(state: StatePlanExecute) -> str:
        info = state.get("contract_info", {}) or {}
        check_result = info.get("check_result", {})
        retry_count = int(info.get("retry_count", 0))

        is_pass = False
        if isinstance(check_result, dict):
            is_pass = bool(check_result.get("is_pass", False))

        # 检查通过，直接进入输出
        if is_pass:
            return "pass"
        # 超过最大重试次数（例如 3 次）后不再打回，直接进入输出，由输出节点提示人工复核
        if retry_count >= 3:
            return "pass"

        # 其余情况继续打回重写
        return "retry"

    # 串联工作流节点与条件边
    workflow.add_edge(START, "input")

    # 从提取节点根据 is_complete 决定后续走向：
    # - 若信息不完整（is_complete 为 False），则直接结束，由 extract_node 的 response 提示用户补充后重新输入；
    # - 若信息完整，则继续进入澄清 / RAG / 写作等后续节点。
    def route_after_extract(state: StatePlanExecute) -> str:
        info = state.get("contract_info", {}) or {}
        is_complete = bool(info.get("is_complete", False))
        return "complete" if is_complete else "incomplete"

    workflow.add_conditional_edges(
        "input",
        route_after_extract,
        {
            "incomplete": END,
            "complete": "add",
        },
    )
    workflow.add_edge("add", "category")
    workflow.add_edge("category", "RAG")
    workflow.add_edge("RAG", "write")
    workflow.add_edge("write", "check")
    workflow.add_conditional_edges(
        "check",
        route_check,
        {
            # 检查通过：进入输出节点，由输出节点统一构造最终 response
            "pass": "output",
            # 检查不通过：打回写作节点，根据建议重新生成说明
            "retry": "write",
        },
    )
    # 输出节点执行完后结束整个流程
    workflow.add_edge("output", END)

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    # 可选：本地调试时生成工作流图，失败时忽略
    try:
        app.get_graph().draw_mermaid_png(output_file_path="workflow.png")
    except Exception:
        pass

    return app


async def start():
    """本地调试入口：直接运行一轮 workflow，打印各节点输出。"""
    app = build_contracts_explanation_app()

    # Demo：单轮调用，若 is_complete 为 False，会在 extract_node 阶段直接返回缺失字段提示并 END，
    #       调用方收到 response 后可提示用户补充信息并重新调用本流程。
    config = {"configurable": {"recursion_limit": 50, "thread_id": "1"}}
    first_input = {"input": "如何判定一起伤害案是“故意杀人”还是“过失伤人”"}

    async for event in app.astream(first_input, config=config, stream_mode="updates"):
        for key, value in event.items():
            if key != "__end__":
                print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(start())
