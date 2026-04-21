from .base import BaseFileException

class FileTypeError(BaseFileException):
    """文件类型不支持异常"""
    def __init__(self, suffix: str, detail: str = None):
        super().__init__(
            code=4001, 
            message=f"不支持的文件格式: {suffix}", 
            detail=detail
        )

class FileMD5MismatchError(BaseFileException):
    """MD5 校验失败异常"""
    def __init__(self, file_name: str,detail: str = None):
        super().__init__(
            code=4002,
            message=f"文件 {file_name} 校验失败，内容可能损坏",
            detail=detail
        )
class FileNotFoundError(BaseFileException):
    """文件不存在异常"""
    def __init__(self, file_name: str, detail: str = None):
        super().__init__(
            code=4003,
            message=f"找不到文件: {file_name}",
            detail=detail
        )

class DirectoryNotFoundError(BaseFileException):
    """目录不存在异常"""
    def __init__(self, dir_name: str, detail: str = None):
        super().__init__(
            code=4004,
            message=f"找不到目录: {dir_name}",
            detail=detail
        )
class FilePermissionError(BaseFileException):
    """文件权限不足异常"""
    def __init__(self, file_name: str, detail: str = None):
        super().__init__(
            code=4005,
            message=f"无权操作文件: {file_name}，请检查系统权限",
            detail=detail
        )

class FileInUseError(BaseFileException):
    """文件被占用异常"""
    def __init__(self, file_name: str, detail: str = None):
        super().__init__(
            code=4006,
            message=f"文件 {file_name} 正在被另一个进程使用",
            detail=detail
        )
class FileCorruptedError(BaseFileException):
    """文件内容损坏异常"""
    def __init__(self, file_name: str, detail: str = None):
        super().__init__(
            code=4007,
            message=f"文件 {file_name} 内容格式非法，无法解析",
            detail=detail
        )
