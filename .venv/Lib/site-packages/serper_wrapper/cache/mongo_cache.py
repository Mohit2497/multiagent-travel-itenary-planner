from __future__ import annotations
import json
import time
import hashlib
from typing import Any, Dict, Optional

import pymongo

from serper_wrapper.cache.base import CacheInterface
from serper_wrapper.exceptions import CacheError


class MongoCache(CacheInterface):
    """MongoDB缓存实现类"""

    def __init__(self, 
                 mongo_uri: str = "mongodb://localhost:27017", 
                 db_name: str = "serper_cache", 
                 collection_name: str = "cache",
                 expiration_time: int = 3600,
                 connect_on_init: bool = True,
                 max_pool_size: int = 100,
                 min_pool_size: int = 0):
        """
        初始化MongoDB缓存
        
        Args:
            mongo_uri: MongoDB连接URI
            db_name: 数据库名称
            collection_name: 集合名称
            expiration_time: 缓存过期时间（秒）
            connect_on_init: 是否在初始化时就连接到MongoDB
            max_pool_size: 连接池最大连接数
            min_pool_size: 连接池最小连接数
        """
        super().__init__(expiration_time)
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self._client = None
        self._db = None
        self._collection = None
        self._connected = False
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        
        # 如果设置立即连接，则尝试连接
        if connect_on_init:
            try:
                self._connect()
            except Exception as e:
                # 初始化连接失败不应该阻止对象创建，但应该记录错误
                print(f"警告: 初始化MongoDB连接失败: {e}")
        
    def _connect(self):
        """连接到MongoDB"""
        if not self._connected:
            try:
                # 使用连接池配置
                self._client = pymongo.MongoClient(
                    self.mongo_uri,
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size
                )
                self._db = self._client[self.db_name]
                self._collection = self._db[self.collection_name]
                
                # 检查是否已存在timestamp索引，如果不存在则创建
                existing_indexes = self._collection.index_information()
                timestamp_index_exists = any(
                    'timestamp' in index_info.get('key', []) 
                    for index_info in existing_indexes.values()
                )
                
                if not timestamp_index_exists:
                    self._collection.create_index("timestamp")
                    
                # 设置连接标志
                self._connected = True
            except Exception as e:
                self._connected = False
                raise CacheError(f"连接MongoDB失败: {e}")

    def _generate_key(self, payload: Dict) -> str:
        """生成缓存键"""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.md5(payload_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从MongoDB获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        if not self._connected:
            self._connect()
        
        try:
            result = self._collection.find_one({"_id": key})
            
            if result is None:
                return None
                
            timestamp = result.get("timestamp")
            if timestamp is None or self._is_expired(timestamp):
                self.delete(key)
                return None
                
            return result.get("data")
        except pymongo.errors.AutoReconnect:
            # 自动重连错误，尝试重新连接
            self._connected = False
            self._connect()
            return self.get(key)  # 递归调用
        except Exception as e:
            raise CacheError(f"从MongoDB获取缓存失败: {e}")

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        将数据缓存到MongoDB
        
        Args:
            key: 缓存键
            value: 要缓存的数据
        """
        if not self._connected:
            self._connect()
        
        try:
            document = {
                "_id": key,
                "timestamp": time.time(),
                "data": value
            }
            
            self._collection.replace_one({"_id": key}, document, upsert=True)
        except pymongo.errors.AutoReconnect:
            # 自动重连错误，尝试重新连接
            self._connected = False
            self._connect()
            self.set(key, value)  # 递归调用
        except Exception as e:
            raise CacheError(f"缓存数据到MongoDB失败: {e}")

    def delete(self, key: str) -> None:
        """
        删除缓存数据
        
        Args:
            key: 缓存键
        """
        if not self._connected:
            self._connect()
        
        try:
            self._collection.delete_one({"_id": key})
        except pymongo.errors.AutoReconnect:
            # 自动重连错误，尝试重新连接
            self._connected = False
            self._connect()
            self.delete(key)  # 递归调用
        except Exception as e:
            raise CacheError(f"从MongoDB删除缓存失败: {e}")

    def clear(self) -> None:
        """清空所有缓存"""
        if not self._connected:
            self._connect()
        
        try:
            self._collection.delete_many({})
        except pymongo.errors.AutoReconnect:
            # 自动重连错误，尝试重新连接
            self._connected = False
            self._connect()
            self.clear()  # 递归调用
        except Exception as e:
            raise CacheError(f"清空MongoDB缓存失败: {e}")

    def cleanup_expired(self) -> None:
        """清理所有过期的缓存项"""
        if not self._connected:
            self._connect()
        
        try:
            expiration_timestamp = time.time() - self.expiration_time
            self._collection.delete_many({"timestamp": {"$lt": expiration_timestamp}})
        except pymongo.errors.AutoReconnect:
            # 自动重连错误，尝试重新连接
            self._connected = False
            self._connect()
            self.cleanup_expired()  # 递归调用
        except Exception as e:
            raise CacheError(f"清理过期缓存失败: {e}")
            
    def close(self):
        """关闭MongoDB连接"""
        if self._connected and self._client:
            try:
                self._client.close()
                self._connected = False
            except Exception as e:
                raise CacheError(f"关闭MongoDB连接失败: {e}")
                
    def __del__(self):
        """析构函数，确保连接被关闭"""
        try:
            self.close()
        except:
            # 在析构函数中不抛出异常
            pass 