from pathlib import Path

from langchain_core.tools import tool
from app.modules.rag.services.rag_service import RagSummarizeService
from app.core.config import settings
from app.shared.exception.file import FileNotFoundError
rag_service = RagSummarizeService()

@tool(description="这是一个检索工具，用于从向量数据库中检索相关文档。输入是一个查询字符串，输出是与查询相关的文档列表。")
async def rag_sammarize_tool(query: str) -> str:
    """异步检索工具：从向量数据库中检索相关文档并总结。"""
    return await rag_service.asummarize(query)
external_data = {}
def generate_external_data() -> str:
    if not external_data:
        external_data_path = settings.agent.external_data_path
        if not Path(external_data_path).exists():
            raise FileNotFoundError(f"外部数据文件未找到: {external_data_path}")
        with open(external_data_path, 'r', encoding='utf-8') as f:
            for line in f:
                user_id,feature,efficiency,consumables,comparison,time = line.strip().replace('"', '').split(',')
                if user_id not in external_data:
                    external_data[user_id] = {}
                external_data[user_id][time] = {
                    '特征': feature,
                    '效率': efficiency,
                    '耗材': consumables,
                    '对比': comparison
                }

@tool(description="这是一个获取外部数据的工具。输入是用户ID和月份，输出是模拟的外部数据结果。")
def fetch_external_data(user_id: str,month: str) -> str:
    """
    这是一个模拟的外部数据获取工具。输入是用户ID和月份，输出是模拟的外部数据结果。
    :param user_id: 用户ID
    :param month: 月份
    :return: 模拟的外部数据结果
    """
    generate_external_data()
    try:
        return external_data[user_id][month]
    except KeyError:
        raise KeyError(f"未找到用户ID {user_id} 在月份 {month} 的外部数据。请确保数据文件中包含该信息。")

if __name__ == '__main__':

    print(fetch_external_data("1004","2025-05"))