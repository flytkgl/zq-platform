"""
用户信息缓存模块

将用户的动态权限信息（role_ids, dept_id, is_superuser）缓存到 Redis，
中间件从 Redis 获取而非从 JWT token 中读取，确保角色变更后权限立即生效。

缓存 key: user_info:{user_id}
缓存内容: {"role_ids": [...], "dept_id": "...", "is_superuser": true/false}
默认 TTL: 300秒（5分钟），缓存未命中时从数据库加载
"""
import json
from typing import Optional, Dict, Any, List

from utils.redis import RedisClient

USER_INFO_CACHE_PREFIX = "user_info:"
USER_INFO_CACHE_TTL = 300  # 5分钟


async def get_cached_user_info(user_id: str) -> Optional[Dict[str, Any]]:
    """
    从 Redis 获取用户信息缓存
    
    :param user_id: 用户ID
    :return: 用户信息字典，未命中返回 None
    """
    redis = await RedisClient.get_client()
    value = await redis.get(f"{USER_INFO_CACHE_PREFIX}{user_id}")
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


async def set_cached_user_info(
    user_id: str,
    role_ids: List[str],
    dept_id: Optional[str],
    is_superuser: bool
) -> None:
    """
    写入用户信息缓存到 Redis
    
    :param user_id: 用户ID
    :param role_ids: 角色ID列表
    :param dept_id: 部门ID
    :param is_superuser: 是否超级管理员
    """
    redis = await RedisClient.get_client()
    data = json.dumps({
        "role_ids": role_ids,
        "dept_id": dept_id,
        "is_superuser": is_superuser,
    }, ensure_ascii=False)
    await redis.set(
        f"{USER_INFO_CACHE_PREFIX}{user_id}",
        data,
        ex=USER_INFO_CACHE_TTL
    )


async def delete_cached_user_info(user_id: str) -> None:
    """
    删除用户信息缓存（角色/部门等变更时调用）
    
    :param user_id: 用户ID
    """
    redis = await RedisClient.get_client()
    await redis.delete(f"{USER_INFO_CACHE_PREFIX}{user_id}")


async def delete_all_cached_user_info() -> None:
    """
    删除所有用户信息缓存（角色权限配置变更时调用）
    """
    redis = await RedisClient.get_client()
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=f"{USER_INFO_CACHE_PREFIX}*", count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


async def load_user_info_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """
    从数据库加载用户信息并写入缓存
    
    :param user_id: 用户ID
    :return: 用户信息字典，用户不存在返回 None
    """
    from app.database import AsyncSessionLocal
    from core.user.service import UserService
    
    async with AsyncSessionLocal() as db:
        user = await UserService.get_by_id(db, user_id)
        if not user:
            return None
        
        role_ids = await UserService.get_user_role_ids(db, user_id)
        
        info = {
            "role_ids": role_ids,
            "dept_id": user.dept_id,
            "is_superuser": user.is_superuser,
        }
        
        # 写入缓存
        await set_cached_user_info(user_id, role_ids, user.dept_id, user.is_superuser)
        
        return info
