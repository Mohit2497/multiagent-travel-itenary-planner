from __future__ import annotations
import json
import requests
import time
from typing import Dict, Any, Union, Optional

from prometheus_client import Counter, Histogram, push_to_gateway, CollectorRegistry

from serper_wrapper.cache import CacheInterface, DiskCache
from serper_wrapper.cache.mongo_cache import MongoCache
from serper_wrapper.exceptions import SerperAPIError, CacheError


class SerperClient:
    """Serper API 客户端类"""
    
    BASE_URL = "https://google.serper.dev/search"
    
    def __init__(
        self, 
        api_key: str,
        cache_type: str = "disk", 
        cache_expiration: int = 3600,
        max_cache_size_mb: int = 4096,
        cache_dir: str = ".serper_cache",
        mongo_uri: str = "mongodb://localhost:27017",
        mongo_db: str = "serper_cache",
        mongo_collection: str = "cache",
        mongo_connect_on_init: bool = True,
        mongo_max_pool_size: int = 100,
        mongo_min_pool_size: int = 0,
        metrics_gateway: str = None,
        metrics_job: str = "serper_wrapper"
    ):
        """
        初始化Serper API客户端
        
        Args:
            api_key: Serper API密钥
            cache_type: 缓存类型，可选值: "disk", "mongo", "none"
            cache_expiration: 缓存过期时间（秒）
            max_cache_size_mb: 磁盘缓存最大大小（MB）
            cache_dir: 磁盘缓存目录
            mongo_uri: MongoDB连接URI
            mongo_db: MongoDB数据库名称
            mongo_collection: MongoDB集合名称
            mongo_connect_on_init: 是否在初始化时连接MongoDB
            mongo_max_pool_size: MongoDB连接池最大连接数
            mongo_min_pool_size: MongoDB连接池最小连接数
            metrics_gateway: Prometheus PushGateway地址，如果不为None则启用指标推送
            metrics_job: 推送到Prometheus的作业名称
        """
        self.api_key = api_key
        self.cache_type = cache_type.lower()
        self.metrics_gateway = metrics_gateway
        self.metrics_job = metrics_job
        
        # 初始化缓存
        self.cache = self._init_cache(
            cache_type=cache_type,
            cache_expiration=cache_expiration,
            max_cache_size_mb=max_cache_size_mb,
            cache_dir=cache_dir,
            mongo_uri=mongo_uri,
            mongo_db=mongo_db,
            mongo_collection=mongo_collection,
            mongo_connect_on_init=mongo_connect_on_init,
            mongo_max_pool_size=mongo_max_pool_size,
            mongo_min_pool_size=mongo_min_pool_size
        )
        
        # 初始化Prometheus指标
        self._init_metrics()
    
    def _init_metrics(self):
        """初始化Prometheus监控指标"""
        if self.metrics_gateway:
            self.registry = CollectorRegistry()
            
            # 创建计数器和直方图
            self.search_counter = Counter(
                'serper_search_total', 
                'Serper API搜索总次数', 
                ['source', 'cache_hit', 'country', 'language'],
                registry=self.registry
            )
            
            self.search_duration = Histogram(
                'serper_search_duration_seconds', 
                'Serper API搜索耗时（秒）',
                ['source', 'cache_hit'],
                registry=self.registry
            )
            
            self.search_error_counter = Counter(
                'serper_search_errors_total', 
                'Serper API搜索错误总次数',
                ['source', 'error_type'],
                registry=self.registry
            )
            
            self.metrics_initialized = True
        else:
            self.metrics_initialized = False
    
    def _push_metrics(self):
        """将指标推送到Prometheus PushGateway"""
        if self.metrics_initialized and self.metrics_gateway:
            try:
                push_to_gateway(self.metrics_gateway, job=self.metrics_job, registry=self.registry)
            except Exception as e:
                # 指标推送失败不应影响主功能
                # 在生产中静默处理错误，但在测试环境中可能需要了解失败原因
                if 'unittest' in __import__('sys').modules:
                    print(f"Warning: Metrics push failed: {e}")
                pass
    
    def _init_cache(
        self, 
        cache_type: str,
        cache_expiration: int,
        max_cache_size_mb: int,
        cache_dir: str,
        mongo_uri: str,
        mongo_db: str,
        mongo_collection: str,
        mongo_connect_on_init: bool = True,
        mongo_max_pool_size: int = 100,
        mongo_min_pool_size: int = 0
    ) -> Optional[CacheInterface]:
        """初始化缓存实例"""
        cache_type = cache_type.lower()
        
        if cache_type == "none":
            return None
        elif cache_type == "disk":
            return DiskCache(
                cache_dir=cache_dir,
                max_size_mb=max_cache_size_mb,
                expiration_time=cache_expiration
            )
        elif cache_type == "mongo":
            return MongoCache(
                mongo_uri=mongo_uri,
                db_name=mongo_db,
                collection_name=mongo_collection,
                expiration_time=cache_expiration,
                connect_on_init=mongo_connect_on_init,
                max_pool_size=mongo_max_pool_size,
                min_pool_size=mongo_min_pool_size
            )
        else:
            raise ValueError(f"不支持的缓存类型: {cache_type}，可选值: disk, mongo, none")
    
    def search(
        self, 
        query: str,
        source: str,
        country: str = "us",
        language: str = "en",
        time_period: str = None,
        num_results: int = 10,
        page: int = 1,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        执行Serper搜索查询
        
        Args:
            query: 搜索查询
            source: 调用来源标记，用于指标统计
            country: 搜索国家代码，例如"us", "jp", "cn"等
            language: 搜索语言代码，例如"en", "zh-cn", "ja"等
            time_period: 搜索时间范围，可选值: "1h", "1d", "1w", "1m", "1y", None(表示任何时间)
            num_results: 返回的搜索结果数量，最大为100
            page: 搜索结果页码
            use_cache: 是否使用缓存
            
        Returns:
            Serper API的响应结果
        """
        # 构建请求参数
        payload = {
            "q": query,
            "gl": country,
            "hl": language,
            "num": min(num_results, 100),  # 最大限制为100
            "page": page
        }
        
        # 添加时间参数
        if time_period:
            tbs_value = self._convert_time_period(time_period)
            if tbs_value:
                payload["tbs"] = tbs_value
        
        start_time = time.time()
        cache_hit = False
        error_type = None
        
        # 检查缓存
        cache_key = None
        if self.cache and use_cache:
            cache_key = self._get_cache_key(payload)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                cache_hit = True
                
                # 记录指标
                if self.metrics_initialized:
                    self.search_counter.labels(
                        source=source, 
                        cache_hit='true',
                        country=country,
                        language=language
                    ).inc()
                    
                    self.search_duration.labels(
                        source=source,
                        cache_hit='true'
                    ).observe(time.time() - start_time)
                    
                    self._push_metrics()
                
                return cached_result
        
        # 发送API请求
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_type = f"http_{response.status_code}"
                raise SerperAPIError(
                    status_code=response.status_code,
                    message=response.text
                )
            
            result = response.json()
            
            # 缓存结果
            if self.cache and use_cache and cache_key:
                self.cache.set(cache_key, result)
            
            # 记录指标
            if self.metrics_initialized:
                self.search_counter.labels(
                    source=source,
                    cache_hit='false',
                    country=country,
                    language=language
                ).inc()
                
                self.search_duration.labels(
                    source=source,
                    cache_hit='false'
                ).observe(time.time() - start_time)
                
                self._push_metrics()
            
            return result
            
        except SerperAPIError as e:
            # 记录错误指标
            if self.metrics_initialized:
                self.search_error_counter.labels(
                    source=source,
                    error_type=error_type or 'api_error'
                ).inc()
                self._push_metrics()
            raise
        except requests.RequestException as e:
            # 记录错误指标
            if self.metrics_initialized:
                self.search_error_counter.labels(
                    source=source,
                    error_type='request_error'
                ).inc()
                self._push_metrics()
            raise SerperAPIError(message=str(e))
        except Exception as e:
            # 记录错误指标
            if self.metrics_initialized:
                self.search_error_counter.labels(
                    source=source,
                    error_type='unknown_error'
                ).inc()
                self._push_metrics()
            raise
    
    def _convert_time_period(self, time_period: str) -> Optional[str]:
        """
        将时间周期字符串转换为Serper API的tbs参数
        
        Args:
            time_period: 时间周期字符串，可选值: "1h", "1d", "1w", "1m", "1y"
            
        Returns:
            tbs参数值，如果无效则返回None
        """
        time_map = {
            "1h": "qdr:h",    # 过去1小时
            "1d": "qdr:d",    # 过去24小时
            "1w": "qdr:w",    # 过去7天
            "1m": "qdr:m",    # 过去一个月
            "1y": "qdr:y"     # 过去一年
        }
        
        return time_map.get(time_period)
    
    def _get_cache_key(self, payload: Dict) -> str:
        """
        根据请求参数生成缓存键
        
        Args:
            payload: 请求参数
            
        Returns:
            缓存键（MD5哈希）
        """
        if isinstance(self.cache, DiskCache):
            return self.cache._generate_key(payload)
        elif isinstance(self.cache, MongoCache):
            return self.cache._generate_key(payload)
        else:
            import hashlib
            payload_str = json.dumps(payload, sort_keys=True)
            return hashlib.md5(payload_str.encode()).hexdigest()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self.cache:
            self.cache.clear()
    
    def custom_search(self, payload: Dict[str, Any], source: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        使用自定义参数执行Serper搜索
        
        Args:
            payload: 自定义请求参数
            source: 调用来源标记，用于指标统计
            use_cache: 是否使用缓存
            
        Returns:
            Serper API的响应结果
        """
        start_time = time.time()
        cache_hit = False
        error_type = None
        country = payload.get("gl", "us")
        language = payload.get("hl", "en")
        
        # 检查缓存
        cache_key = None
        if self.cache and use_cache:
            cache_key = self._get_cache_key(payload)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                cache_hit = True
                
                # 记录指标
                if self.metrics_initialized:
                    self.search_counter.labels(
                        source=source, 
                        cache_hit='true',
                        country=country,
                        language=language
                    ).inc()
                    
                    self.search_duration.labels(
                        source=source,
                        cache_hit='true'
                    ).observe(time.time() - start_time)
                    
                    self._push_metrics()
                
                return cached_result
        
        # 发送API请求
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            # 检查响应状态
            if response.status_code != 200:
                error_type = f"http_{response.status_code}"
                raise SerperAPIError(
                    status_code=response.status_code,
                    message=response.text
                )
            
            result = response.json()
            
            # 缓存结果
            if self.cache and use_cache and cache_key:
                self.cache.set(cache_key, result)
            
            # 记录指标
            if self.metrics_initialized:
                self.search_counter.labels(
                    source=source,
                    cache_hit='false',
                    country=country,
                    language=language
                ).inc()
                
                self.search_duration.labels(
                    source=source,
                    cache_hit='false'
                ).observe(time.time() - start_time)
                
                self._push_metrics()
            
            return result
            
        except SerperAPIError as e:
            # 记录错误指标
            if self.metrics_initialized:
                self.search_error_counter.labels(
                    source=source,
                    error_type=error_type or 'api_error'
                ).inc()
                self._push_metrics()
            raise
        except requests.RequestException as e:
            # 记录错误指标
            if self.metrics_initialized:
                self.search_error_counter.labels(
                    source=source,
                    error_type='request_error'
                ).inc()
                self._push_metrics()
            raise SerperAPIError(message=str(e))
        except Exception as e:
            # 记录错误指标
            if self.metrics_initialized:
                self.search_error_counter.labels(
                    source=source,
                    error_type='unknown_error'
                ).inc()
                self._push_metrics()
            raise 
    
    def __del__(self):
        """析构函数，确保资源被正确释放"""
        # 关闭MongoDB连接
        if self.cache and isinstance(self.cache, MongoCache):
            try:
                self.cache.close()
            except:
                # 在析构函数中不抛出异常
                pass 