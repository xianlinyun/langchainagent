import re
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.config import settings

class SplitterFactory:
    @staticmethod
    def legal_document_loader(text: str, law_name: str, source: str | None = None) -> list[Document]:
        """按编-章-节-条层级解析法律文本，并以“条”为最小分块单元。"""
        numeral = r"[一二三四五六七八九十百千万0-9]+"
        part_pattern = re.compile(rf"^第({numeral})编[\s\u3000]*(.*)$")
        chapter_pattern = re.compile(rf"^第({numeral})章[\s\u3000]*(.*)$")
        section_pattern = re.compile(rf"^第({numeral})节[\s\u3000]*(.*)$")
        article_pattern = re.compile(rf"^第({numeral})条[\s\u3000]*(.*)$")

        documents: list[Document] = []
        current_part = "未分编"
        current_chapter = "未分章"
        current_section = "未分节"

        current_article_no: str | None = None
        current_article_lines: list[str] = []

        # 从 source 反推出完整目录分类，并构造层级列表：
        # 例如 data/law/civil/labor/xxx.docx ->
        # ["law", "law/civil", "law/civil/labor"]
        category_levels: list[str] = []
        if source:
            try:
                data_root = Path(settings.chroma.data_path).resolve()
                rel = Path(source).resolve().relative_to(data_root)
                if rel.parent != Path("."):
                    category_str = str(rel.parent).replace("\\", "/")
                    parts = category_str.split("/")
                    category_levels = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
            except Exception:
                # source 不在 data_root 下或解析失败时，忽略分类信息
                category_levels = []

        def normalize_title(title: str) -> str:
            # 清理全角空格/多空格，避免出现“总　　则”这类展示噪声
            return re.sub(r"[\s\u3000]+", "", title or "").strip() or "未命名"

        def normalize_body_line(line: str) -> str:
            """规范正文行空白，避免向量中夹杂大段空格。

            - 合并连续空格/全角空格为单个半角空格；
            - 保留原有标点和编号结构。"""
            # 先去掉首尾空白，再压缩行内多余空白
            line = line.strip()
            return re.sub(r"[ \t\u3000]+", " ", line)

        def flush_article():
            nonlocal current_article_no, current_article_lines
            if not current_article_no:
                return
            content = "\n".join(current_article_lines).strip()
            if content:
                context_line = f"《{law_name}》 {current_part} > {current_chapter} > {current_section}"
                # 构造精简后的 metadata：只保留真实存在的层级，过滤“未分编/未分章/未分节”占位信息
                metadata = {
                    "law_name": law_name,
                    "article": current_article_no,
                    "source": source or law_name,
                }
                if category_levels:
                    metadata["category"] = category_levels
                if current_part != "未分编":
                    metadata["part"] = current_part
                if current_chapter != "未分章":
                    metadata["chapter"] = current_chapter
                if current_section != "未分节":
                    metadata["section"] = current_section
                documents.append(
                    Document(
                        page_content=f"{context_line}\n{content}",
                        metadata=metadata,
                    )
                )
            current_article_no = None
            current_article_lines = []

        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue

            # 统一规范正文行中的多余空白
            line = normalize_body_line(line)

            part_match = part_pattern.match(line)
            if part_match:
                flush_article()
                part_title = normalize_title(part_match.group(2))
                if part_title == "未命名":
                    part_title = f"第{part_match.group(1)}编"
                current_part = f"第{part_match.group(1)}编" + part_title
                current_chapter = "未分章"
                current_section = "未分节"
                continue

            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                flush_article()
                chapter_title = normalize_title(chapter_match.group(2))
                if chapter_title == "未命名":
                    chapter_title = f"第{chapter_match.group(1)}章"
                current_chapter = f"第{chapter_match.group(1)}章" + chapter_title
                current_section = "未分节"
                continue

            section_match = section_pattern.match(line)
            if section_match:
                flush_article()
                section_title = normalize_title(section_match.group(2))
                if section_title == "未命名":
                    section_title = f"第{section_match.group(1)}节"
                current_section = f"第{section_match.group(1)}节" + section_title
                continue

            article_match = article_pattern.match(line)
            if article_match:
                flush_article()
                current_article_no = f"第{article_match.group(1)}条"
                first_line = current_article_no
                article_tail = article_match.group(2).strip()
                if article_tail:
                    first_line = f"{first_line} {article_tail}"
                first_line = normalize_body_line(first_line)
                current_article_lines = [first_line]
                continue

            if current_article_no:
                current_article_lines.append(line)

        flush_article()
        return documents

    @staticmethod
    def get_default_splitter() -> RecursiveCharacterTextSplitter:
        """针对普通通用文档的切分器"""
        return RecursiveCharacterTextSplitter(
            chunk_size=settings.chroma.chunk_size,
            chunk_overlap=settings.chroma.chunk_overlap
        )