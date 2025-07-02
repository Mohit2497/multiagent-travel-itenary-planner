from __future__ import annotations
from abc import ABC, abstractmethod
import time
from typing import Any, Optional, Dict


class CacheInterface(ABC):
    """缓存接口基类，所有缓存实现必须继承此类"""

    def __init__(self, expiration_time: int = 3600):
        """
        初始化缓存接口
        
        Args:
            expiration_time: 缓存过期时间（秒），默认1小时
        """
        self.expiration_time = expiration_time

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 要缓存的数据
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清空所有缓存"""
        pass

    def _is_expired(self, timestamp: float) -> bool:
        """
        检查缓存是否过期
        
        Args:
            timestamp: 缓存创建时间戳
            
        Returns:
            如果缓存已过期则返回True，否则返回False
        """
        return time.time() - timestamp > self.expiration_time 