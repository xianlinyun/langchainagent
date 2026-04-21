

from pathlib import Path
from app.core.config import settings
from app.utils.file import check_md5_hex, save_md5_hex
from app.utils.file_handler import get_file_md5_hex, listdir_with_allowed_types
from app.utils.logger_handler import get_logger
logger = get_logger(__name__)
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

def remove_document_by_file(self, file_path: Path | str) -> dict:
    """删除指定文件在向量库中的分块，并移除对应 MD5 记录。"""
    raw = str(file_path).strip()
    input_path = Path(raw)
    data_root = Path(settings.chroma.data_path).resolve()

    candidate_sources: set[str] = set()
    if input_path.is_absolute():
        candidate_sources.add(str(input_path.resolve()))
    else:
        candidate_sources.add(str((data_root / input_path).resolve()))

    # 回退匹配：支持仅文件名或 data 下相对路径输入
    result_all = self.vector_store.get(include=["metadatas"])
    metadatas = result_all.get("metadatas", []) or []
    normalized_input = raw.replace("\\", "/").lstrip("/")
    input_name = input_path.name

    for meta in metadatas:
        source = str((meta or {}).get("source", ""))
        if not source:
            continue
        source_norm = source.replace("\\", "/")

        if source in candidate_sources:
            candidate_sources.add(source)
            continue
        if normalized_input and source_norm.endswith("/" + normalized_input):
            candidate_sources.add(source)
            continue
        if input_name and Path(source).name == input_name:
            candidate_sources.add(source)

    deleted_ids: set[str] = set()
    md5_removed = False
    matched_sources: list[str] = []

    for source in sorted(candidate_sources):
        result = self.vector_store.get(where={"source": source}, include=["metadatas"])
        ids = result.get("ids", []) or []
        if not ids:
            continue

        self.vector_store.delete(ids=ids)
        deleted_ids.update(ids)
        matched_sources.append(source)

        src_path = Path(source)
        file_md5 = get_file_md5_hex(src_path) if src_path.exists() else None
        md5_removed = self._remove_md5_record(file_md5) or md5_removed

    logger.info(
        f"删除文件索引完成: input={raw} | matched_sources={len(matched_sources)} | deleted_chunks={len(deleted_ids)} | md5_removed={md5_removed}"
    )
    return {
        "input": raw,
        "matched_sources": matched_sources,
        "deleted_chunks": len(deleted_ids),
        "md5_removed": md5_removed,
    }
def check_md5(md5_for_check: str) -> bool:
    if not md5_for_check:
        logger.warning("未配置 chroma.md5_hex_store，跳过 MD5 校验")
        return True # 或者根据业务逻辑返回 False
    return check_md5_hex(abs_path=Path(settings.chroma.md5_hex_store), md5_for_check=md5_for_check)
def save_md5(md5_for_check: str):
    if not md5_for_check:
        logger.warning("未配置 chroma.md5_hex_store，跳过 MD5 校验")
        return True # 或者根据业务逻辑返回 False
    return save_md5_hex(abs_path=Path(settings.chroma.md5_hex_store), md5_for_check=md5_for_check)
allowed_files_path: list = listdir_with_allowed_types(Path(settings.chroma.data_path), settings.chroma.allow_knowledge_file_type)
