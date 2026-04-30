from datetime import datetime
import logging
from pathlib import Path
import pathlib
from app.utils.path_tool import get_abs_path

ROOT_LOGGER_NAME = pathlib.Path(__file__).resolve().parents[1].name
LOG_ROOT = get_abs_path("logs")
Path(LOG_ROOT).mkdir(parents=True, exist_ok=True)
DEFAULT_LOG_FORMAT = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)


def setup_logger(
    name: str = "Agent",
    log_file: str = None,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Avoid adding multiple handlers to the logger
    if logger.handlers:
        return logger
    if not log_file:
        log_file = LOG_ROOT / f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"

    # 文件handler
    file_handler = logging.FileHandler(Path(LOG_ROOT) / log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)

    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handler)

    logger = logging.getLogger(name)
    return logger


def get_logger(name: str = "Agent") -> logging.Logger:
    return logging.getLogger(name)


logger = setup_logger("app")

if __name__ == "__main__":
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")
