from __future__ import annotations
import json
import os
import time
import hashlib
from typing import Any, Dict, Optional
import shutil

from serper_wrapper.cache.base import CacheInterface
from serper_wrapper.exceptions import CacheError


class DiskCache(CacheInterface):
    """磁盘缓存实现类"""

    def __init__(self, cache_dir: str = ".serper_cache", max_size_mb: int = 4096, expiration_time: int = 3600):
        """
        初始化磁盘缓存
        
        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大缓存大小，单位MB
            expiration_time: 缓存过期时间（秒）
        """
        super().__init__(expiration_time)
        self.cache_dir = os.path.abspath(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception as e:
            raise CacheError(f"无法创建缓存目录: {e}")

    def _get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"serper_cache_{key}.json")

    def _generate_key(self, payload: Dict) -> str:
        """生成缓存键"""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.md5(payload_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从磁盘获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                
            timestamp = cached_data.get("timestamp")
            if timestamp is None or self._is_expired(timestamp):
                self.delete(key)
                return None
                
            return cached_data.get("data")
        except Exception as e:
            raise CacheError(f"读取缓存文件失败: {e}")

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        将数据缓存到磁盘
        
        Args:
            key: 缓存键
            value: 要缓存的数据
        """
        # 检查缓存大小，如果超过限制则清理
        self._check_cache_size()
        
        cache_path = self._get_cache_path(key)
        
        try:
            cached_data = {
                "timestamp": time.time(),
                "data": value
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cached_data, f, ensure_ascii=False)
        except Exception as e:
            raise CacheError(f"写入缓存文件失败: {e}")

    def delete(self, key: str) -> None:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
        """
        cache_path = self._get_cache_path(key)
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception as e:
                raise CacheError(f"删除缓存文件失败: {e}")

    def clear(self) -> None:
        """清空所有缓存"""
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path) and filename.startswith("serper_cache_"):
                    os.remove(file_path)
        except Exception as e:
            raise CacheError(f"清空缓存失败: {e}")

    def _get_cache_size(self) -> int:
        """
        获取当前缓存大小
        
        Returns:
            当前缓存大小（字节）
        """
        total_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path) and filename.startswith("serper_cache_"):
                    total_size += os.path.getsize(file_path)
        except Exception as e:
            raise CacheError(f"获取缓存大小失败: {e}")
            
        return total_size

    def _check_cache_size(self) -> None:
        """检查缓存大小，如果超过限制则清理最旧的缓存"""
        if self._get_cache_size() >= self.max_size_bytes:
            self._cleanup_old_cache()

    def _cleanup_old_cache(self) -> None:
        """清理最旧的缓存文件，直到缓存大小低于最大限制的80%"""
        target_size = int(self.max_size_bytes * 0.8)
        
        try:
            cache_files = []
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path) and filename.startswith("serper_cache_"):
                    cache_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序
            cache_files.sort(key=lambda x: x[1])
            
            # 删除最旧的文件，直到缓存大小低于目标
            for file_path, _ in cache_files:
                if self._get_cache_size() <= target_size:
                    break
                os.remove(file_path)
        except Exception as e:
            raise CacheError(f"清理缓存失败: {e}") 