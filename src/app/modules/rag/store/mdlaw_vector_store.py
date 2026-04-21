from pathlib import Path
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.llm.factory import get_embedding_model
from app.modules.rag.loaders.load_document import get_file_documents
from app.modules.rag.loaders.util import check_md5, save_md5
from app.modules.rag.process.md_spiliter import markdown_legal_document_loader
from app.utils.file_handler import listdir_with_allowed_types, get_file_md5_hex
from app.utils.logger_handler import get_logger


logger = get_logger(__name__)


class MdLawVectorStoreService:
    """专门针对 Markdown 版法律文本（如 just-laws 中 README.md）的向量库服务。"""

    def __init__(self):
        self.vector_store = Chroma(
            persist_directory=settings.chroma.persist_directory,
            collection_name=settings.chroma.collection_name,
            # 与 law_vector_store 一致，使用外部 embedding_service
            embedding_function=get_embedding_model("BAAI"),
        )
        self.default_splitter = RecursiveCharacterTextSplitter(
            separators=settings.chroma.separatoes,
            chunk_size=settings.chroma.chunk_size,
            chunk_overlap=settings.chroma.chunk_overlap,
            length_function=len,
        )

    def get_retriever(self, category: str | None = None, k: int | None = None):
        """获取检索器，可按需覆盖 k。"""

        search_kwargs = {"k": k or settings.chroma.k}
        if category:
            if category.startswith("law/"):
                search_kwargs["filter"] = {"category": {"$contains": category}}
            else:
                search_kwargs["filter"] = {"category": category}
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

        - 若能从查询中解析出法律名称和条文号，则直接用 where 过滤 Chroma；
        - 命中则不再走向量相似度，直接返回对应 Document；
        - 未命中或无法解析时，返回空列表，由上层回退到语义检索。
        """

        law_name, article_no = self._parse_law_query(query)
        if not article_no:
            return []

        # Chroma 顶层 where 需要只有一个操作符，这里用 $and 组合条件
        conditions: list[dict] = [{"article": article_no}]

        # 若解析出了法律名称，则进一步收窄范围
        if law_name:
            # 存储时 law_name 为完整标题（如“中华人民共和国宪法”），
            # 这里使用 contains 以兼容“宪法”“中华人民共和国宪法”等不同写法。
            conditions.append({"law_name": {"$contains": law_name}})

        where: dict
        if len(conditions) == 1:
            where = conditions[0]
        else:
            where = {"$and": conditions}

        # 直接通过 Chroma 的 where 条件获取对应文档
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

        # 若有精确命中的文档，则只返回这些结果（可再裁剪到 k 条）
        if documents and k:
            return documents[:k]
        return documents

    def retrieve_documents(self, query: str, category: str | None = None, k: int | None = None) -> list[Document]:
        """根据查询语句检索相关文档，返回 Document 列表。

        检索策略：
        1. 优先尝试利用元数据（law_name + article）做精确命中，
           例如 "中华人民共和国宪法第二十条"；
        2. 若未命中，则回退到原有的向量相似度检索，
           并在语义检索阶段为 query 加上指令前缀，
           以更好地适配 BGE 等指令型 embedding 模型。
        """

        # 1) 先尝试按元数据精确检索
        meta_docs = self._retrieve_by_metadata(query, k=k)
        if meta_docs:
            return meta_docs

        # 2) 回退到向量检索
        instruction = "为指令检索相关法律条款："
        query_with_instruction = f"{instruction}{query}"
        retriever = self.get_retriever(category=category, k=k)
        return retriever.invoke(query_with_instruction)

    def _resolve_category(self, file_path: Path) -> str:
        data_root = Path(settings.chroma.data_path)
        try:
            relative_path = file_path.relative_to(data_root)
        except ValueError:
            return file_path.stem

        if relative_path.parent != Path("."):
            return str(relative_path.parent).replace("\\", "/")
        return file_path.stem

    def _enrich_documents_with_category(self, documents, category: str, source_path: Path):
        data_root = Path(settings.chroma.data_path).resolve()
        try:
            rel_path = Path(source_path).resolve().relative_to(data_root)
            source_value = str(rel_path).replace("\\", "/")
        except ValueError:
            source_value = Path(source_path).name

        for doc in documents:
            base_metadata = dict(doc.metadata or {})
            base_metadata.setdefault("category", category)
            base_metadata.setdefault("source", source_value)
            doc.metadata = base_metadata
        return documents

    def _remove_md5_record(self, file_md5: str) -> bool:
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
        data_root = Path(settings.chroma.data_path).resolve()
        input_path = Path(file_path)

        if input_path.is_absolute():
            try:
                rel_path = input_path.resolve().relative_to(data_root)
            except ValueError:
                rel_path = Path(input_path.name)
        else:
            rel_path = input_path

        rel_source = str(rel_path).replace("\\", "/")
        abs_source = str((data_root / rel_path).resolve())

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

        这里主要面向 Markdown 版法律文本（.md）。
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

                # 针对法律类 Markdown 文本，只使用条文级结构化切分；
                # 若无法识别出任何“第X条”，则直接跳过该文件，不再回退为通用分块，
                # 保证向量库中的每条记录都尽量对应单条法条。
                if category.startswith("law"):
                    source_text = documents if isinstance(documents, str) else "\n".join(
                        doc.page_content for doc in documents if doc.page_content
                    )
                    split_documents = markdown_legal_document_loader(
                        text=source_text,
                        law_name=path.stem,
                        source=str(path),
                    )

                    if not split_documents:
                        logger.warning(f"法律 Markdown 结构化切分结果为空，跳过文件: {path}")
                        continue
                else:
                    if isinstance(documents, str):
                        documents = [Document(page_content=documents, metadata={"source": str(path)})]
                    split_documents = self.default_splitter.split_documents(documents)

                if not split_documents:
                    logger.warning(f"未能从文件中提取到任何分块文档: {path}")
                    continue
                split_documents = self._enrich_documents_with_category(split_documents, category, path)
                self.vector_store.add_documents(split_documents)
                save_md5(md5_hex)
                logger.info(f"成功处理文件并添加到向量库: {path} | category={category} | md5={md5_hex}")
            except Exception as e:
                logger.warning(str(e))


if __name__ == "__main__":
    vs = MdLawVectorStoreService()
    vs.load_document(True)
    docs = vs.retrieve_documents("中华人民共和国宪法 第二十条", k=4)

    for doc in docs:
        print("内容片段：", doc.page_content[:100])
        print("metadata：", doc.metadata)