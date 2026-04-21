
from pathlib import Path

from app.shared.exception.file import FileTypeError
from app.utils.file_handler import pdf_loader, text_loader
from langchain_core.documents import Document
from docx import Document as DocxDocument

from app.utils.logger_handler import get_logger
logger = get_logger(__name__)
def get_file_documents(file_path: Path):
    # 这里你需要根据文件类型来加载文档，这只是一个示例
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return pdf_loader(file_path, passwd=None)
    elif suffix == ".txt":
        return text_loader(file_path)
    elif suffix == ".md":
        # Markdown 文件按纯文本方式加载，后续由 markdown_legal_document_loader 进行法律结构化解析
        return text_loader(file_path)
    elif suffix == ".docx":
        doc = DocxDocument(str(file_path))
        part = "\n".join([p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()])
        return part
    else:
        logger.info(f"不支持的文件类型: {file_path.suffix}")
        raise FileTypeError(file_path.suffix)