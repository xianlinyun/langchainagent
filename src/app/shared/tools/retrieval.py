from pathlib import Path

from langchain_core.tools import tool
from app.modules.rag.services.rag_service import RagSummarizeService
from app.modules.rag.store.law_vector_store import VectorStoreService
from app.core.config import settings
from app.shared.exception.file import FileNotFoundError

rag_service = RagSummarizeService()
vector_store_service = VectorStoreService()


@tool(description="这是一个检索并总结的工具，适合直接问答场景。输入是查询字符串，输出是基于向量库的总结结果。")
async def rag_sammarize_tool(query: str, category: str | None = None, k: int | None = None) -> str:
    """异步检索工具：从向量数据库中检索相关文档并用 LLM 总结。"""
    return await rag_service.asummarize(query, category, k)


@tool(description="这是一个仅检索的工具，返回原始文档片段，适合在 Agent 中由大模型自行阅读并作答。")
def rag_retrieve_tool(query: str, category: str | None = None, law_name: str | None = None, article: str | None = None, k: int | None = None) -> str:
    """向量检索工具：返回与查询相关的文档片段及来源信息。"""
    docs = vector_store_service.retrieve_documents(query=query, category=category, law_name=law_name, article=article, k=k)
    if not docs:
        return "未找到相关文档。"

    parts: list[str] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        source = metadata.get("source", "未知")

        # 补充 law_name / article / category 等关键信息，方便大模型精确引用法律条文
        law_name = metadata.get("law_name")
        article = metadata.get("article")
        categories = metadata.get("category")
        if isinstance(categories, list):
            categories_str = ", ".join(str(c) for c in categories)
        else:
            categories_str = str(categories) if categories is not None else ""

        header_bits: list[str] = []
        if law_name:
            header_bits.append(f"法律名称: {law_name}")
        if article:
            header_bits.append(f"条文: {article}")
        if categories_str:
            header_bits.append(f"分类: {categories_str}")

        meta_line = "；".join(header_bits) if header_bits else "(无结构化元数据)"

        parts.append(
            f"[参考资料{idx}] 元数据: {meta_line}\n"
            f"内容片段: {doc.page_content}\n"
            f"来源: {source}"
        )

    return "\n\n".join(parts)


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
                    '对比': comparison,
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