"""
Redis缓存模块
提供Redis连接管理和缓存操作工具类
"""
import json
from typing import Optional, Any, Union, List
from contextlib import asynccontextmanager

from redis import asyncio as aioredis
from redis.asyncio import Redis

from app.config import settings


class RedisClient:
    """Redis客户端管理器"""
    
    _client: Optional[Redis] = None
    
    @classmethod
    async def get_client(cls) -> Redis:
        """获取Redis客户端实例（单例模式）"""
        if cls._client is None:
            cls._client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._client
    
    @classmethod
    async def close(cls) -> None:
        """关闭Redis连接"""
        if cls._client:
            await cls._client.close()
            cls._client = None


class CacheManager:
    """
    缓存管理器
    提供通用的缓存操作方法
    """
    
    def __init__(self, prefix: str = ""):
        """
        初始化缓存管理器
        
        :param prefix: 缓存key前缀（会自动添加全局前缀）
        """
        self.prefix = f"{settings.CACHE_PREFIX}{prefix}"
    
    def _make_key(self, key: str) -> str:
        """生成完整的缓存key"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        :param key: 缓存key
        :return: 缓存值，不存在返回None
        """
        client = await RedisClient.get_client()
        value = await client.get(self._make_key(key))
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        设置缓存
        
        :param key: 缓存key
        :param value: 缓存值（自动JSON序列化）
        :param expire: 过期时间（秒），默认使用配置值
        :return: 是否成功
        """
        client = await RedisClient.get_client()
        expire = expire or settings.CACHE_DEFAULT_EXPIRE
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        elif not isinstance(value, str):
            value = json.dumps(value, default=str)
        
        return await client.set(self._make_key(key), value, ex=expire)
    
    async def delete(self, key: str) -> int:
        """
        删除缓存
        
        :param key: 缓存key
        :return: 删除的key数量
        """
        client = await RedisClient.get_client()
        return await client.delete(self._make_key(key))
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        根据模式删除缓存
        
        :param pattern: 匹配模式（如 user:*）
        :return: 删除的key数量
        """
        client = await RedisClient.get_client()
        full_pattern = self._make_key(pattern)
        keys = []
        async for key in client.scan_iter(match=full_pattern):
            keys.append(key)
        
        if keys:
            return await client.delete(*keys)
        return 0
    
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        :param key: 缓存key
        :return: 是否存在
        """
        client = await RedisClient.get_client()
        return await client.exists(self._make_key(key)) > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间
        
        :param key: 缓存key
        :param seconds: 过期时间（秒）
        :return: 是否成功
        """
        client = await RedisClient.get_client()
        return await client.expire(self._make_key(key), seconds)
    
    async def ttl(self, key: str) -> int:
        """
        获取剩余过期时间
        
        :param key: 缓存key
        :return: 剩余秒数，-1表示永不过期，-2表示不存在
        """
        client = await RedisClient.get_client()
        return await client.ttl(self._make_key(key))
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        自增
        
        :param key: 缓存key
        :param amount: 增加量
        :return: 增加后的值
        """
        client = await RedisClient.get_client()
        return await client.incrby(self._make_key(key), amount)
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """
        自减
        
        :param key: 缓存key
        :param amount: 减少量
        :return: 减少后的值
        """
        client = await RedisClient.get_client()
        return await client.decrby(self._make_key(key), amount)
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """获取Hash字段值"""
        client = await RedisClient.get_client()
        value = await client.hget(self._make_key(name), key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def hset(self, name: str, key: str, value: Any) -> int:
        """设置Hash字段值"""
        client = await RedisClient.get_client()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        elif not isinstance(value, str):
            value = json.dumps(value, default=str)
        return await client.hset(self._make_key(name), key, value)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除Hash字段"""
        client = await RedisClient.get_client()
        return await client.hdel(self._make_key(name), *keys)
    
    async def hgetall(self, name: str) -> dict:
        """获取Hash所有字段"""
        client = await RedisClient.get_client()
        data = await client.hgetall(self._make_key(name))
        result = {}
        for k, v in data.items():
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                result[k] = v
        return result
    
    async def lpush(self, key: str, *values: Any) -> int:
        """列表左侧插入"""
        client = await RedisClient.get_client()
        serialized = [
            json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list)) else str(v)
            for v in values
        ]
        return await client.lpush(self._make_key(key), *serialized)
    
    async def rpush(self, key: str, *values: Any) -> int:
        """列表右侧插入"""
        client = await RedisClient.get_client()
        serialized = [
            json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list)) else str(v)
            for v in values
        ]
        return await client.rpush(self._make_key(key), *serialized)
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表范围"""
        client = await RedisClient.get_client()
        values = await client.lrange(self._make_key(key), start, end)
        result = []
        for v in values:
            try:
                result.append(json.loads(v))
            except json.JSONDecodeError:
                result.append(v)
        return result


# 默认缓存管理器实例
cache = CacheManager()


async def get_redis() -> Redis:
    """FastAPI依赖注入用：获取Redis客户端"""
    return await RedisClient.get_client()
