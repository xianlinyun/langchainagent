from pathlib import Path
import hashlib
from app.utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader,TextLoader
#计算文件的MD5值
def get_file_md5_hex(file_path: Path) -> str:
    if not file_path.exists():
        logger.error(f"文件路径无效: {file_path}")
        return None
    if not file_path.is_file():
        logger.error(f"文件不存在: {file_path}")
        return None
    chunk_size = 4096
    md5_hash = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
            return md5_hash.hexdigest()
    except Exception as e:
        logger.error(f"计算文件MD5失败: {e}")
        return None
#获取目录下指定类型的文件列表
def listdir_with_allowed_types(dir_path: Path, allowed_types: list) -> list:
    if not dir_path.is_dir():
        raise FileNotFoundError(f"目录不存在: {dir_path}")
    try:
        normalized_types = {suffix.lower() for suffix in allowed_types}
        return [
            f for f in dir_path.rglob("*")
            if f.is_file() and f.suffix.lower() in normalized_types
        ]
    except Exception as e:
        raise Exception(f"列出目录文件失败: {e}")
#加载PDF文件并返回Document对象列表
def load_pdf_as_documents(file_path: Path) -> list:
    if not file_path.exists():
        logger.error(f"文件路径无效: {file_path}")
        return []
    if not file_path.is_file():
        logger.error(f"文件不存在: {file_path}")
        return []
    try:
        loader = PyPDFLoader(str(file_path))
        return loader.load()
    except Exception as e:
        logger.error(f"加载PDF文件失败: {e}")
        return []
def pdf_loader(file_path: Path,passwd: str) -> list:
    return PyPDFLoader(file_path,passwd).load()
def text_loader(file_path: Path) -> list:
    return TextLoader(file_path, encoding='utf-8').load()
