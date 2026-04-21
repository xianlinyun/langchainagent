import re
from pathlib import Path

from langchain_core.documents import Document

from app.core.config import settings


def markdown_legal_document_loader(text: str, law_name: str, source: str | None = None) -> list[Document]:
	"""针对 Markdown 版法律文本的切分器。

	支持类似 just-laws 中的 README.md：
	- 章节使用 Markdown 标题：``## 第一章 总则``；
	- 条文使用加粗：``**第一条** 具体内容``；
	- 以“条”为最小分块单元。
	"""

	# 若 Markdown 顶部存在一级标题，且形式为 "# 中华人民共和国 ..."，
	# 则优先使用该标题作为 law_name；否则退回调用方传入的文件名/目录名。
	law_name_from_heading: str | None = None
	for raw in text.splitlines():
		line = raw.strip()
		if not line:
			continue
		# 精确匹配以 "# 中华人民共和国 " 开头的一级标题
		if line.startswith("# 中华人民共和国") or line.startswith("# 全国人民代表大会") and len(line) <= 100:
			law_name_from_heading = line.lstrip("#").strip()
			break
	if law_name_from_heading:
		law_name = law_name_from_heading

	numeral = r"[一二三四五六七八九十百千万0-9]+"

	# 允许前缀 Markdown 标题/加粗标记
	part_pattern = re.compile(rf"^(?:#+\\s*)?第({numeral})编[\\s\\u3000]*(.*)$")
	chapter_pattern = re.compile(rf"^(?:#+\\s*)?第({numeral})章[\\s\\u3000]*(.*)$")
	section_pattern = re.compile(rf"^(?:#+\\s*)?第({numeral})节[\\s\\u3000]*(.*)$")
	# 条文行放宽为：只要一行中包含“第X条”即可视为一条，
	# 避免因隐藏字符或 Markdown 组合标记导致严格行首匹配失败。
	article_pattern = re.compile(rf"第({numeral})条")

	documents: list[Document] = []
	current_part = "未分编"
	current_chapter = "未分章"
	current_section = "未分节"

	current_article_no: str | None = None
	current_article_lines: list[str] = []

	# 从 source 反推出完整目录分类，并构造层级列表
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
			category_levels = []

	def normalize_title(title: str) -> str:
		# 清理全角空格/多空格，避免出现“总　　则”这类展示噪声
		return re.sub(r"[\\s\\u3000]+", "", title or "").strip() or "未命名"

	def normalize_body_line(line: str) -> str:
		"""规范正文行空白，避免向量中夹杂大段空格。"""
		line = line.strip()
		return re.sub(r"[ \t\\u3000]+", " ", line)

	def flush_article() -> None:
		nonlocal current_article_no, current_article_lines
		if not current_article_no:
			return
		content = "\n".join(current_article_lines).strip()
		if content:
			# 为避免作用域问题，使用局部“生效值”，不要在此处修改外层变量
			effective_category_levels = category_levels or ["未分类"]
			effective_part = "" if current_part == "未分编" else current_part
			effective_chapter = "" if current_chapter == "未分章" else current_chapter
			effective_section = "" if current_section == "未分节" else current_section

			metadata: dict = {
				"law_name": law_name,
				"article": current_article_no,
				"source": source or law_name,
			}
			if effective_category_levels:
				metadata["category"] = effective_category_levels
			if effective_part:
				metadata["part"] = effective_part
			if effective_chapter:
				metadata["chapter"] = effective_chapter
			if effective_section:
				metadata["section"] = effective_section

			context_line = f"《{law_name}》{effective_part}{effective_chapter}{effective_section}"
			documents.append(
				Document(
					page_content=f"{context_line}\n{content}",
					metadata=metadata,
				)
			)
		current_article_no = None
		current_article_lines = []

	in_frontmatter = False

	for raw in text.splitlines():
		stripped = raw.strip()
		if not stripped:
			continue

		# 跳过 YAML frontmatter
		if stripped == "---":
			in_frontmatter = not in_frontmatter
			continue
		if in_frontmatter:
			continue

		line = stripped

		# 去掉 Markdown 列表前缀，如 "- ", "* "
		line = re.sub(r"^[\-*+]\\s+", "", line)

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

		article_match = article_pattern.search(line)
		if article_match:
			flush_article()
			current_article_no = f"第{article_match.group(1)}条"
			# 直接使用规范化后的整行作为首行，保留全部条文内容。
			first_line = normalize_body_line(line)
			current_article_lines = [first_line]
			continue

		if current_article_no:
			current_article_lines.append(line)

	flush_article()
	return documents

