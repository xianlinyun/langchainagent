from app.modules.rag.store.law_vector_store import VectorStoreService
from app.utils.prompt_loader import load_rag_prompt
from langchain_core.prompts import PromptTemplate
from app.core.llm.factory import get_chat_model
from langchain_core.output_parsers import StrOutputParser
import asyncio
class RagSummarizeService:
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        self.retriever = self.vector_store_service.get_retriever()
        self.model = get_chat_model()
        self.prompts = load_rag_prompt()
        self.prompt_template = PromptTemplate.from_template(self.prompts)
        self.chain = self._build_chain()

    def print_prompt(self, prompt):
        print("当前对话模板:")
        print(prompt.to_string())
        return prompt

    def _build_chain(self):
        chain = self.prompt_template | self.model | StrOutputParser()
        return chain

    def _is_law_query(self, query: str) -> bool:
        keywords = [
            "民法典",
            "合同",
            "劳动法",
            "劳动合同法",
            "刑法",
            "宪法",
            "条",
            "章",
            "编",
            "法律",
            "法规",
        ]
        return any(keyword in query for keyword in keywords)

    # 这里的 query 是用户输入的查询，返回值是相关文档列表（同步接口）
    def retrieve(self, query: str,category: str | None = None, k: int | None = None):
        # 统一按 data/law 下所有法律目录检索：
        # 只要判定为“法律类问题”，就将 category 固定为 "law"，
        # 依赖向量库中文档 metadata["category"] 中的层级列表
        # （例如 ["law", "law/criminal-law", ...]）+ Chroma 的 $contains
        # 来实现只在法律语料中检索。
        category = "law" if self._is_law_query(query) else None
        # 法律类问题适当放大 k，提高召回概率
        top_k = 20 if category else None

        # 先按分类检索
        relevant_docs = self.vector_store_service.retrieve_documents(
            query=query,
            category=category,
            k=top_k,
        )

        # 若分类过滤导致召回为空，自动降级为全库检索，避免误杀。
        if not relevant_docs and category is not None:
            relevant_docs = self.vector_store_service.retrieve_documents(
                query=query,
                category=None,
                k=top_k,
            )
        return relevant_docs

    # ---------------- 异步接口 ----------------
    async def aretrieve(self, query: str, category: str | None = None, k: int | None = None):
        """异步检索封装，目前内部仍使用同步向量库检索。

        如后续引入真正的异步向量库，可在此改为 await 调用。
        """
        # 同步调用保持不变，仅作为 async 包装，避免阻塞调用方签名
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.retrieve, query, category, k)

    async def asummarize(self, query: str,category: str | None = None, k: int | None = None) -> str:
        """异步总结接口：用于在 async agent / workflow 中调用。"""
        relevant_docs = await self.aretrieve(query, category, k)
        if not relevant_docs:
            return "未找到相关文档。"

        context = "\n\n".join(
            [
                f"[参考资料{idx + 1}]:{doc.page_content} | 参考源: {doc.metadata.get('source', '未知')}"
                for idx, doc in enumerate(relevant_docs)
            ]
        )
        # 使用异步 LLM 调用
        result = await self.chain.ainvoke({"input": query, "context": context})
        return result

    # 兼容保留原同步 summarize 接口
    def summarize(self, query: str) -> str:
        """同步总结接口：供老代码使用。"""
        relevant_docs = self.retrieve(query)
        if not relevant_docs:
            return "未找到相关文档。"

        context = "\n\n".join(
            [
                f"[参考资料{idx + 1}]:{doc.page_content} | 参考源: {doc.metadata.get('source', '未知')}"
                for idx, doc in enumerate(relevant_docs)
            ]
        )
        return self.chain.invoke({"input": query, "context": context})


if __name__ == "__main__":
    rag_service = RagSummarizeService()
    query = "借贷"
    summary = rag_service.summarize(query)
    print(summary)
