from pathlib import Path
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.llm.factory import get_embedding_model
from app.modules.rag.loaders.load_document import get_file_documents
from app.modules.rag.loaders.util import check_md5, save_md5
from app.modules.rag.process.splitter import SplitterFactory
from app.utils.file_handler import listdir_with_allowed_types, get_file_md5_hex
from app.utils.logger_handler import get_logger
logger = get_logger(__name__)
class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            persist_directory=settings.chroma.persist_directory,
            collection_name=settings.chroma.collection_name,
            # 使用外部 embedding_service 计算向量，避免在本进程重复加载 BAAI 模型
            embedding_function=get_embedding_model(),
        )
        self.default_splitter = RecursiveCharacterTextSplitter(
            separators=settings.chroma.separatoes,
            chunk_size=settings.chroma.chunk_size,
            chunk_overlap=settings.chroma.chunk_overlap,
            length_function=len,
        )
        self.law_splitter = SplitterFactory.legal_document_loader

    def get_retriever(self, category: str | None = None, law_name: str | None = None, article: str | None = None, k: int | None = None):
        """获取检索器，可按需覆盖 k。

        - category 为 None 时，全库检索；
        - 当 category 为 "law/civil" 这类层级路径时，
          依赖元数据中统一的 category 列表 + Chroma 的 $contains 进行过滤：
            * 文档写入时，category 统一为层级列表，例如
              ["law", "law/civil", "law/civil/labor"]；
            * 检索时使用 {"category": {"$contains": category}} 做包含匹配。

        注意：新版 Chroma 要求 where/filter 的顶层只包含一个“操作符”键，
        因此当需要组合多个条件时，必须显式使用 $and 包装。
        """

        search_kwargs = {"k": k or settings.chroma.k}

        # 收集各个字段对应的过滤条件
        filters: list[dict] = []
        if category:
            # 统一使用 $contains 过滤，依赖元数据中的 category 列表
            filters.append({"category": {"$contains": category}})
        if law_name:
            # 使用 law_name 进行精确匹配
            filters.append({"law_name": law_name})
        if article:
            # 使用 article 进行精确匹配
            filters.append({"article": article})

        # 根据条件数量构造符合 Chroma 约束的 filter 结构
        if len(filters) == 1:
            search_kwargs["filter"] = filters[0]
        elif len(filters) > 1:
            search_kwargs["filter"] = {"$and": filters}

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def _parse_law_query(self, query: str) -> tuple[str | None, str | None]:
        """从查询中解析出法律名称和条文号（第X条）。

        支持示例：
        - "中华人民共和国宪法第二十条"
        - "《中华人民共和国宪法》第二十条"
        - "宪法第二十条"
        - "根据宪法第二十条的规定……" 等
        """

        if not query:
            return None, None

        text = query.strip()

        # 先找出“第X条”
        numeral = r"[一二三四五六七八九十百千万0-9]+"
        m_article = re.search(rf"第({numeral})条", text)
        if not m_article:
            return None, None

        article_no = f"第{m_article.group(1)}条"

        # 取出“第X条”之前的内容，尽量解析为法律名称
        before = text[: m_article.start()].strip()
        if not before:
            return None, article_no

        # 去掉引号、书名号等包装
        before = before.strip("《》\"' “”")

        # 常见后缀关键字，尽量只保留到“法/条例/规定/宪法/组织法/基本法”等
        law_suffix_pattern = re.compile(
            r"(.+?(?:法|条例|规定|宪法|组织法|基本法|细则|办法))"
        )
        m_law = law_suffix_pattern.search(before)
        law_name = m_law.group(1).strip() if m_law else before

        return law_name or None, article_no

    def _retrieve_by_metadata(self, query: str, k: int | None = None) -> list[Document]:
        """优先利用 law_name + article 元数据做精确命中。

        - 若能从查询中解析出法律名称和条文号，则先按 article 过滤 Chroma；
        - 再在 Python 侧用包含关系筛选 law_name；
        - 命中则不再走向量相似度，直接返回对应 Document；
        - 未命中或无法解析时，返回空列表，由上层回退到语义检索。
        """

        law_name, article_no = self._parse_law_query(query)
        if not article_no:
            return []

        # 只在 Chroma 里按 article 过滤，避免在存储层使用 $contains
        # 对字符串字段 law_name 做模糊匹配时，由 Python 侧自行筛选，
        # 以兼容 "宪法" / "中华人民共和国宪法" 等不同写法。
        where = {"article": article_no}

        try:
            result = self.vector_store.get(
                where=where,
                include=["documents", "metadatas"],
            )
        except Exception as e:
            logger.warning(f"按元数据检索失败: query={query!r}, where={where!r}, error={e}")
            return []

        docs_raw = result.get("documents") or []
        metas = result.get("metadatas") or []

        documents: list[Document] = []
        for content, meta in zip(docs_raw, metas):
            if not content:
                continue
            documents.append(Document(page_content=content, metadata=meta or {}))

        # 若解析出了法律名称，则在 Python 侧进一步用包含关系筛选 law_name
        if law_name:
            filtered: list[Document] = []
            for doc in documents:
                name = str((doc.metadata or {}).get("law_name", ""))
                # 兼容 "宪法" ⊂ "中华人民共和国宪法"、
                # 以及完全相等或反向包含等多种写法。
                if law_name in name or name in law_name:
                    filtered.append(doc)
            if filtered:
                documents = filtered

        # 若有精确命中的文档，则只返回这些结果（可再裁剪到 k 条）
        if documents and k:
            return documents[:k]
        return documents

    def retrieve_documents(self, query: str, category: str | None = None, law_name: str | None = None, article: str | None = None, k: int | None = None) -> list[Document]:
        """根据查询语句检索相关文档，返回 Document 列表。

        检索策略：
        1. 若 query 中包含 "第X条"，优先尝试利用元数据（law_name + article）做精确命中；
        2. 若未命中，则回退到原有的向量相似度检索。
        """

        # 1) 先尝试按元数据精确检索（主要针对法律条文类查询）
        meta_docs = self._retrieve_by_metadata(query, k=k)
        if meta_docs:
            return meta_docs

        # 2) 回退到向量检索
        retriever = self.get_retriever(category=category, law_name=law_name, article=article, k=k)
        # 兼容新版 LangChain：VectorStoreRetriever 使用 invoke 调用
        return retriever.invoke(query)




    def _resolve_category(self, file_path: Path) -> str:
        """根据文件路径推断分类。优先使用相对目录，其次使用文件名。

        这里保留完整目录层级，例如：
        - law/civil/labor/中华人民共和国劳动法_20181229.docx
          -> category="law/civil/labor"。

        检索阶段通过前缀匹配支持按上层目录（如 "law/civil"）聚合查询，
        不再在这里截断路径，避免丢失子类别信息。"""

        data_root = Path(settings.chroma.data_path)
        try:
            relative_path = file_path.relative_to(data_root)
        except ValueError:
            return file_path.stem

        if relative_path.parent != Path("."):
            return str(relative_path.parent).replace("\\", "/")
        return file_path.stem

    def _build_category_hierarchy(self, category: str | None) -> list[str]:
        """将单个分类路径转换为层级列表。

        例如:
        - "law/civil/labor" -> ["law", "law/civil", "law/civil/labor"]
        - "faq" -> ["faq"]
        """

        if not category:
            return []

        parts = category.split("/")
        hierarchy: list[str] = []
        for i in range(len(parts)):
            hierarchy.append("/".join(parts[: i + 1]))

        # 去重保序
        seen: set[str] = set()
        result: list[str] = []
        for item in hierarchy:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def _enrich_documents_with_category(self, documents, category: str, source_path: Path):
        data_root = Path(settings.chroma.data_path).resolve()
        try:
            rel_path = Path(source_path).resolve().relative_to(data_root)
            source_value = str(rel_path).replace("\\", "/")
        except ValueError:
            # 不在 data_root 下的文件，退化为文件名
            source_value = Path(source_path).name

        category_list = self._build_category_hierarchy(category)

        for doc in documents:
            base_metadata = dict(doc.metadata or {})

            # 合并上游可能已有的 category（字符串或列表）
            existing_cat = base_metadata.get("category")
            merged: list[str] = []
            if isinstance(existing_cat, list):
                merged.extend(str(c) for c in existing_cat)
            elif isinstance(existing_cat, str):
                merged.extend(self._build_category_hierarchy(existing_cat))

            merged.extend(category_list)

            # 去重保序
            seen_cat: set[str] = set()
            final_cat: list[str] = []
            for c in merged:
                if c and c not in seen_cat:
                    seen_cat.add(c)
                    final_cat.append(c)

            if final_cat:
                base_metadata["category"] = final_cat

            # 统一使用相对 data_root 的路径，便于跨环境迁移
            base_metadata.setdefault("source", source_value)
            doc.metadata = base_metadata
        return documents

    def _remove_md5_record(self, file_md5: str) -> bool:
        """从 MD5 存储文件中移除指定文件哈希。"""
        if not file_md5:
            return False

        md5_store_path = Path(settings.chroma.md5_hex_store)
        if not md5_store_path.exists() or not md5_store_path.is_file():
            return False

        lines = md5_store_path.read_text(encoding="utf-8").splitlines()
        new_lines = [line for line in lines if line.strip().lower() != file_md5.lower()]
        removed = len(new_lines) != len(lines)
        md5_store_path.write_text(
            "\n".join(new_lines) + ("\n" if new_lines else ""),
            encoding="utf-8",
        )
        return removed

    def remove_document(self, file_path: str):
        """
        根据文件路径移除向量库中的文档
        :param file_path: 文件路径
        :return: None
        """
        data_root = Path(settings.chroma.data_path).resolve()
        input_path = Path(file_path)

        if input_path.is_absolute():
            try:
                rel_path = input_path.resolve().relative_to(data_root)
            except ValueError:
                rel_path = Path(input_path.name)
        else:
            rel_path = input_path

        # 与存储时保持一致的相对路径写法
        rel_source = str(rel_path).replace("\\", "/")
        abs_source = str((data_root / rel_path).resolve())

        # 同时兼容旧数据里可能残留的绝对路径 source
        where = {"source": {"$in": [rel_source, abs_source]}}
        result = self.vector_store.get(where=where, include=["metadatas"])
        ids = result.get("ids", []) or []

        deleted_chunks = 0
        if ids:
            self.vector_store.delete(ids=ids)
            deleted_chunks = len(ids)

        file_abs_path = (data_root / rel_path).resolve()
        file_md5 = get_file_md5_hex(file_abs_path) if file_abs_path.exists() else None
        md5_removed = self._remove_md5_record(file_md5)

        logger.info(
            f"删除文件索引完成: {file_path} | deleted_chunks={deleted_chunks} | md5_removed={md5_removed}"
        )
        return {
            "source": rel_source,
            "deleted_chunks": deleted_chunks,
            "md5_removed": md5_removed,
        }


    def load_document(self, force_reload: bool = False):
        """递归扫描 data 目录下允许类型的文件，写入向量库，并使用 md5.text 做去重。

        MD5 记录文件由 settings.chroma.md5_hex_store 指定，当前即 src/md5.text。
        - 默认 `force_reload=False`：按 MD5 去重，已导入文件会被跳过；
        - 当需要调整 chunk_size / 分词策略后重建向量库时，可传入
            `force_reload=True`，忽略 MD5 直接重建当前 data 下所有文件的向量。
        """

        data_root = Path(settings.chroma.data_path)
        allowed_files_path: list[Path] = listdir_with_allowed_types(
            data_root,
            settings.chroma.allow_knowledge_file_type,
        )

        for path in allowed_files_path:
            md5_hex = get_file_md5_hex(path)
            if not force_reload and check_md5(md5_hex):
                logger.info(f"文件已存在，跳过处理: {path}")
                continue

            try:
                documents = get_file_documents(path)
                if not documents:
                    logger.warning(f"未能从文件中提取到任何文档: {path}")
                    continue

                category = self._resolve_category(path)
                if category.startswith("law"):
                    source_text = documents if isinstance(documents, str) else "\n".join(
                        doc.page_content for doc in documents if doc.page_content
                    )
                    split_documents = self.law_splitter(
                        text=source_text,
                        law_name=path.stem,
                        source=str(path),
                    )
                else:
                    if isinstance(documents, str):
                        documents = [Document(page_content=documents, metadata={"source": str(path)})]
                    split_documents = self.default_splitter.split_documents(documents)

                if not split_documents:
                    logger.warning(f"未能从文件中提取到任何分块文档: {path}")
                    continue
                split_documents = self._enrich_documents_with_category(split_documents, category, path)
                self.vector_store.add_documents(split_documents)
                # 即使 force_reload 也写入一次，确保 md5.text 与现有向量状态一致
                save_md5(md5_hex)
                logger.info(f"成功处理文件并添加到向量库: {path} | category={category} | md5={md5_hex}")
            except Exception as e:
                logger.warning(str(e))
if __name__ == '__main__': 
    vs = VectorStoreService()
    # vs.remove_document("src/app/modules/rag/data/law/civil/民法典-合同编.docx")
    # vs.load_document(True)
    # 示例：仅在刑法目录下检索
    docs = vs.retrieve_documents("民间借贷 利率 月息叁厘 法律规定 民法典", category="law/economic/accounting-law", k=3)

    for doc in docs:
        print("内容片段：", doc.page_content[:100])
        print("metadata：", doc.metadata)