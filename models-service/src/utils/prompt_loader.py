from app.utils.logger_handler import logger
from app.core.config import settings


def load_system_prompt():
    try:
        system_prompt_path = settings.prompts.main_prompt_path
    except KeyError as e:
        raise KeyError(f"配置文件缺少必要的键: {e}")
    try:
        return open(system_prompt_path, "r", encoding="utf-8").read()
    except FileNotFoundError:
        raise FileNotFoundError(f"系统提示文件未找到: {system_prompt_path}")

def load_prompt(prompt: str):
    """通用提示词加载器。

    参数 `prompt` 可以是：
    - settings.prompts 中配置的键名，例如 "main_prompt_path"；
    - 也可以是一个直接的文件路径（绝对或相对）。
    """

    # 优先按配置键查找，查不到则直接把入参当路径使用
    try:
        prompt_path = settings.prompts[prompt]
    except Exception:
        prompt_path = prompt

    try:
        return open(prompt_path, "r", encoding="utf-8").read()
    except FileNotFoundError:
        logger.error(f"提示文件未找到: {prompt_path}")
        raise FileNotFoundError(f"提示文件未找到: {prompt_path}")
def load_rag_prompt():
    try:
        rag_summarize_prompt_path = settings.prompts.rag_summarize_prompt_path
    except KeyError as e:
        logger.error(f"配置文件缺少必要的键: {e}")
        raise KeyError(f"配置文件缺少必要的键: {e}")
    try:
        return open(rag_summarize_prompt_path, "r", encoding="utf-8").read()
    except FileNotFoundError:
        logger.error(f"RAG总结提示文件未找到: {rag_summarize_prompt_path}")
        raise FileNotFoundError(f"RAG总结提示文件未找到: {rag_summarize_prompt_path}")


def load_report_prompt():
    try:
        # report_prompt_path = get_abs_path(conf['prompts']['report_prompt_path'])
        report_prompt_path = settings.prompts.report_prompt_path
    except KeyError as e:
        logger.error(f"配置文件缺少必要的键: {e}")
        raise KeyError(f"配置文件缺少必要的键: {e}")
    try:
        return open(report_prompt_path, "r", encoding="utf-8").read()
    except FileNotFoundError:
        logger.error(f"报告提示文件未找到: {report_prompt_path}")
        raise FileNotFoundError(f"报告提示文件未找到: {report_prompt_path}")
def load_law_prompt():
    try:
        law_prompt_path = settings.prompts.law_prompt_path
    except KeyError as e:
        logger.error(f"配置文件缺少必要的键: {e}")
        raise KeyError(f"配置文件缺少必要的键: {e}")
    try:
        return open(law_prompt_path, "r", encoding="utf-8").read()
    except FileNotFoundError:
        logger.error(f"法律提示文件未找到: {law_prompt_path}")
        raise FileNotFoundError(f"法律提示文件未找到: {law_prompt_path}")
