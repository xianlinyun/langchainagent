# src/app/core/llm/chains/contract_chains.py

from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm.factory import get_chat_model
from app.utils.prompt_loader import load_prompt

def get_llm_chain(path: Path | str,format: str = "jinja2"):
    """
    抽象化：获取生成的执行链
    """
    # 1. 加载模板 (建议封装一个 load_prompt 工具函数)
    prompt_content = load_prompt(path)
    
    prompt = ChatPromptTemplate.from_template(
        prompt_content,
        template_format=format
    )
    
    # 2. 绑定模型（可以根据需要切换模型）
    llm = get_chat_model() 
    
    # 3. 组装 Chain
    # 使用 StrOutputParser 直接输出字符串，方便 Node 处理
    return prompt | llm | StrOutputParser()
