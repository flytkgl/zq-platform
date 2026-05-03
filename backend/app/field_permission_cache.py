"""
字段权限缓存管理
使用 Redis 缓存字段权限配置，提高查询性能
"""
from typing import Dict, List, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession

from utils.redis import RedisClient


class FieldPermissionCache:
    """字段权限缓存管理器"""
    
    # 缓存键前缀
    CACHE_PREFIX = "field_perm"
    
    # 缓存过期时间（秒）
    CACHE_TTL = 3600  # 1小时
    
    @classmethod
    def _get_cache_key(cls, role_id: str, resource_type: str) -> str:
        """生成缓存键"""
        return f"{cls.CACHE_PREFIX}:{role_id}:{resource_type}"
    
    @classmethod
    def _get_roles_cache_key(cls, role_ids: List[str], resource_type: str) -> str:
        """生成多角色缓存键"""
        sorted_role_ids = sorted(role_ids)
        roles_str = "_".join(sorted_role_ids)
        return f"{cls.CACHE_PREFIX}:roles:{roles_str}:{resource_type}"
    
    @classmethod
    async def get(
        cls,
        role_id: str,
        resource_type: str
    ) -> Optional[List[Dict]]:
        """
        从缓存获取字段权限配置
        
        :param role_id: 角色ID
        :param resource_type: 资源类型
        :return: 字段权限配置列表，如果不存在返回 None
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return None
        
        cache_key = cls._get_cache_key(role_id, resource_type)
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                return None
        
        return None
    
    @classmethod
    async def set(
        cls,
        role_id: str,
        resource_type: str,
        configs: List[Dict]
    ) -> None:
        """
        设置字段权限配置到缓存
        
        :param role_id: 角色ID
        :param resource_type: 资源类型
        :param configs: 字段权限配置列表
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return
        
        cache_key = cls._get_cache_key(role_id, resource_type)
        cache_data = json.dumps(configs, ensure_ascii=False)
        
        await redis_client.setex(
            cache_key,
            cls.CACHE_TTL,
            cache_data
        )
    
    @classmethod
    async def get_merged(
        cls,
        role_ids: List[str],
        resource_type: str
    ) -> Optional[Dict[str, Dict]]:
        """
        从缓存获取合并后的字段权限配置
        
        :param role_ids: 角色ID列表
        :param resource_type: 资源类型
        :return: 合并后的字段权限配置字典
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return None
        
        cache_key = cls._get_roles_cache_key(role_ids, resource_type)
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                return None
        
        return None
    
    @classmethod
    async def set_merged(
        cls,
        role_ids: List[str],
        resource_type: str,
        merged_config: Dict[str, Dict]
    ) -> None:
        """
        设置合并后的字段权限配置到缓存
        
        :param role_ids: 角色ID列表
        :param resource_type: 资源类型
        :param merged_config: 合并后的字段权限配置
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return
        
        cache_key = cls._get_roles_cache_key(role_ids, resource_type)
        cache_data = json.dumps(merged_config, ensure_ascii=False)
        
        await redis_client.setex(
            cache_key,
            cls.CACHE_TTL,
            cache_data
        )
    
    @classmethod
    async def delete(
        cls,
        role_id: str,
        resource_type: str
    ) -> None:
        """
        删除指定角色和资源类型的缓存
        
        :param role_id: 角色ID
        :param resource_type: 资源类型
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return
        
        cache_key = cls._get_cache_key(role_id, resource_type)
        await redis_client.delete(cache_key)
    
    @classmethod
    async def delete_by_role(cls, role_id: str) -> None:
        """
        删除指定角色的所有字段权限缓存
        
        :param role_id: 角色ID
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return
        
        # 删除该角色的所有缓存
        pattern = f"{cls.CACHE_PREFIX}:{role_id}:*"
        keys = await redis_client.keys(pattern)
        
        if keys:
            await redis_client.delete(*keys)
        
        # 删除包含该角色的多角色缓存
        pattern = f"{cls.CACHE_PREFIX}:roles:*"
        keys = await redis_client.keys(pattern)
        
        for key in keys:
            if role_id in key:
                await redis_client.delete(key)
    
    @classmethod
    async def delete_by_resource(cls, resource_type: str) -> None:
        """
        删除指定资源类型的所有字段权限缓存
        
        :param resource_type: 资源类型
        """
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return
        
        # 删除该资源类型的所有缓存
        pattern = f"{cls.CACHE_PREFIX}:*:{resource_type}"
        keys = await redis_client.keys(pattern)
        
        if keys:
            await redis_client.delete(*keys)
    
    @classmethod
    async def clear_all(cls) -> None:
        """清除所有字段权限缓存"""
        try:
            redis_client = await RedisClient.get_client()
        except Exception:
            return
        
        pattern = f"{cls.CACHE_PREFIX}:*"
        keys = await redis_client.keys(pattern)
        
        if keys:
            await redis_client.delete(*keys)
