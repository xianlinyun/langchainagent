import asyncio
from langchain.agents import create_agent
from app.modules.agent.middleware.model import log_before_model
from app.modules.agent.middleware.prompt import report_prompt_switch
from app.modules.agent.middleware.tool import MonitorTool
from app.core.llm.factory import get_chat_model
from app.shared.tools.retrieval import rag_retrieve_tool
from app.utils.prompt_loader import load_law_prompt, load_system_prompt, load_report_prompt
from app.modules.agent.tools.retrieval import (
    fetch_external_data,
    rag_sammarize_tool,
)
from app.modules.agent.tools.services import get_user_location, get_weather
from app.modules.agent.tools.system import (
    fill_context_for_report,
    get_user_id,
    get_month_now,
)


class ReactAgent:
    def __init__(self, config):
        self.agent = create_agent(
            model=get_chat_model(),
            system_prompt=load_law_prompt(),
            tools=[
                rag_retrieve_tool,
                fetch_external_data,
                get_weather,
                get_user_location,
                get_user_id,
                get_month_now,
                fill_context_for_report,
            ],
            middleware=[log_before_model, report_prompt_switch, MonitorTool()],
        )

    async def execute_stream(self, query: str):
        input = {
            "messages": [
                # {"role": "system", "content": load_system_prompt()},
                {"role": "user", "content": query},
            ]
        }
        async for chunk in self.agent.astream(
            input, stream_mode="values", context={"report": False}
        ):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip()


if __name__ == "__main__":
    async def main():
        agent = ReactAgent(config={})
        query = "小明欠小王10000元月息叁厘,请帮我分析一下小明的法律风险，并且帮我写一份催款函。"
        async for response in agent.execute_stream(query):
            print(response, end="", flush=True)

    asyncio.run(main())
