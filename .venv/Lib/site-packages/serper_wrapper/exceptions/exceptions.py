from __future__ import annotations

class SerperException(Exception):
    """基础异常类，所有其他异常继承自此类"""
    pass


class SerperAPIError(SerperException):
    """调用Serper API时发生的错误"""
    
    def __init__(self, status_code=None, message=None):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Serper API错误: {status_code} - {message}")


class CacheError(SerperException):
    """缓存操作时发生的错误"""
    
    def __init__(self, message=None):
        self.message = message
        super().__init__(f"缓存错误: {message}")