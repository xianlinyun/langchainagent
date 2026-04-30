import hashlib
from pathlib import Path
from app.utils.logger_handler import logger


def check_md5_hex(abs_path: Path, md5_for_check: str) -> bool:
    if not abs_path.exists():
        open(abs_path, 'w',encoding='utf-8').close()  # 创建空文件
        return False
    if not abs_path.is_file():
        return False
    try:
        with open(abs_path, 'r') as f:
            hash_md5 = hashlib.md5()
            recorded_md5s = [line.strip().lower() for line in f if line.strip()]
            is_match = md5_for_check in recorded_md5s
            if not is_match:
                logger.error(f"MD5 不匹配! 文件: {abs_path}, 预期: {md5_for_check}, 实际: {recorded_md5s}")
        return is_match
    except PermissionError:
        raise PermissionError(f"权限不足，无法读取文件: {abs_path}")
        return False
    except Exception as e:
        # 捕捉非预期的系统级错误
        logger.exception(f"读取文件并计算 MD5 时发生未知异常: {str(e)}")
        return False


def save_md5_hex(abs_path: Path, md5_for_check: str):
    """将 MD5 写入记录文件，若已存在则不再追加，避免重复行膨胀。"""
    try:
        # 若文件已存在，则先读取已有 MD5 列表，避免重复写入
        existing_md5s = set()
        if abs_path.exists() and abs_path.is_file():
            with open(abs_path, 'r', encoding='utf-8') as f:
                existing_md5s = {line.strip().lower() for line in f if line.strip()}

        if md5_for_check.lower() in existing_md5s:
            return

        # 不存在则追加一行
        with open(abs_path, 'a', encoding='utf-8') as f:
            f.write(md5_for_check + '\n')
    except PermissionError:
        logger.error(f"权限不足，无法写入文件: {abs_path}")
    except Exception as e:
        # 捕捉非预期的系统级错误
        logger.exception(f"写入 MD5 时发生未知异常: {str(e)}")
