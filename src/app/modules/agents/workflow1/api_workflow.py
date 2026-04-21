import operator
from pathlib import Path
from typing import Annotated, TypedDict, Union

from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from app.core.llm.factory import get_chat_model
from app.shared.routers.tool import tool_callback_router
from app.shared.states.plan import Plan, PlanExecute
from app.utils.prompt_loader import load_system_prompt, load_prompt,load_law_prompt
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
import asyncio
from langchain.agents import create_agent
from app.utils.prompt_loader import load_prompt
from langgraph.checkpoint.memory import MemorySaver
from app.shared.tools.retrieval import (
    fetch_external_data,
    rag_sammarize_tool,
)
agent = create_agent(
    model=get_chat_model(),
    system_prompt='',
    tools=[rag_sammarize_tool],
)
memory = MemorySaver()
planner_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        load_prompt("src/app/shared/prompts/planner.jinja2"),
        template_format="jinja2",
    ),
    MessagesPlaceholder(variable_name="messages"),
])

planner = planner_prompt | agent
class Response(BaseModel):
    response: str
class Act(BaseModel):
    action: Union[Response, Plan] = Field(
        description="要执行的行为.如果要回应用户,请使用response字段.如果要进一步使用tools获取答案,请使用plan字段"
)
replanner_prompt_template = load_prompt("src/app/shared/prompts/replanner.jinja2")
replanner_prompt = ChatPromptTemplate.from_template(
    replanner_prompt_template,
    template_format="jinja2",
)
replanner = replanner_prompt | agent

async def start():
    async def plan_step(state: PlanExecute):
        # 调用 planner 得到计划文本
        result = await planner.ainvoke({
            "messages": [{"role": "user", "content": state["input"]}],
        })

        # LangChain agent 通常返回包含 messages 的字典
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            content = result["messages"][-1].content
        else:
            content = str(result)

        # 按行拆成步骤列表，去掉空行
        steps = [line.strip() for line in content.split("\n") if line.strip()]

        return {"plan": steps}
    async def execute_step(state: PlanExecute):
        plan = state["plan"]
        plan_str = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(plan)])
        task = plan[0] 
        task_formatted = f"""对于以下计划:
{plan_str}\n\n你的任务是执行第{1}步: {task}"""
        result = await agent.ainvoke({ "messages": [{"role": "user", "content": task_formatted}] })
        return {"past_steps": state["past_steps"] + [(task, result["messages"][-1].content)]}
    async def replan_step(state: PlanExecute):
        # 使用 input / plan / past_steps 作为 replanner 的输入
        result = await replanner.ainvoke({
            "input": state["input"],
            "plan": "\n".join(state["plan"]),
            "past_steps": state["past_steps"],
        },streaming=True,stream_mode="updates")  # 开启流式输出，及时获取 replanner 的反馈

        # 从返回中提取文本内容
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            content = result["messages"][-1].content
        else:
            content = str(result)

        # 简单停止条件：如果 replanner 认为原计划没问题或循环次数已足够，则直接给出最终回复
        if "原计划没有问题" in content or len(state["past_steps"]) >= 2:
            return {"response": content}

        # 否则按行拆成新的计划步骤，继续执行
        steps = [line.strip() for line in content.split("\n") if line.strip()]
        return {"plan": steps}
        

    workflow = StateGraph(PlanExecute)
    workflow.add_node("planner", plan_step)
    workflow.add_node("agent", execute_step)
    workflow.add_node("replanner", replan_step)
    workflow.add_edge(START,"planner")
    workflow.add_edge("planner", "agent")
    workflow.add_edge("agent", "replanner")
    workflow.add_conditional_edges(
        "replanner",
        lambda state: "response" if "response" in state else "plan",
        {
            "response": END,  # 结束
            "plan": "agent",   # 继续执行新计划
        },
    )
    app = workflow.compile(checkpointer=memory)
    gragh = app.get_graph().draw_mermaid_png(output_file_path="workflow.png")

    config = {"configurable": {"recursion_limit": 50, "thread_id": "default"}}
    input = {"input": "1+1=？"}
    async for event in app.astream(input, config=config,stream_mode="updates"):
        for key, value in event.items():
            if key != "__end__":
                print(f"{key}: {value}")
if __name__ == "__main__":
    asyncio.run(start())