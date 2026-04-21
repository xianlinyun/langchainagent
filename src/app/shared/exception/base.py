class BaseException(Exception):
    """所有业务异常的基类"""
    def __init__(self, code: int, message: str, detail: str = None):
        self.code = code      # 业务错误码 (如 10001)
        self.message = message  # 展示给用户的友好信息
        self.detail = detail    # 调试用的详细信息 (可选)
        super().__init__(message)
class BaseFileException(BaseException):
    """文件相关异常的基类"""
    def __init__(self, code: int, message: str, detail: str = None):
        super().__init__(code, message, detail)