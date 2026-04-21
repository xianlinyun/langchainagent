from typing import Callable
from app.utils.logger_handler import get_logger
from langchain.agents.middleware import ModelRequest, dynamic_prompt

from app.utils.prompt_loader import load_law_prompt, load_report_prompt

logger = get_logger(__name__)


@dynamic_prompt  # 每一次生成提示词时都会调用这个函数，可以根据当前的状态动态切换提示词
def report_prompt_switch(request: ModelRequest):
    if request.runtime.context.get("report", False):
        print("*" * 30)
        return load_report_prompt()
    return load_law_prompt()
