#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Permission Utils - 基于API路径的动态权限鉴权

工作原理：
1. 用户访问某个API时，根据请求的路径和方法，查找Permission表中是否有对应的权限记录
2. 如果有权限记录，检查用户的角色是否关联了该权限
3. 如果用户角色有该权限，则放行；否则返回403
4. 如果Permission表中没有该API的权限记录，则默认放行（未配置权限的API不做限制）
"""
import json
import re
from typing import List, Optional, Dict, Any, Set

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from utils.redis import RedisClient

# Redis 缓存 key 前缀和 TTL
API_PERMISSION_CACHE_KEY = "api_permission:path_map"  # Hash: (path:method) -> permission_id
ROLE_PERMISSION_CACHE_PREFIX = "api_permission:role:"  # role_permission:role:{role_id} -> Set[permission_id]
API_PERMISSION_CACHE_TTL = 300  # API路径映射缓存 5分钟
ROLE_PERMISSION_CACHE_TTL = 300  # 角色权限缓存 5分钟


# HTTP方法映射（与Permission模型中的定义一致）
HTTP_METHOD_MAP = {
    'GET': 0,
    'POST': 1,
    'PUT': 2,
    'DELETE': 3,
    'PATCH': 4,
    'ALL': 5,
}


class APIPermissionChecker:
    """
    基于API路径的动态权限检查器
    
    在AuthMiddleware中调用，根据请求的API路径和方法检查用户是否有权限
    """
    
    def __init__(self):
        pass
    
    async def load_permissions_cache(self, db: AsyncSession):
        """
        加载所有API权限到 Redis 缓存
        
        建议在应用启动时调用，或者定期刷新
        """
        from core.permission.model import Permission
        
        result = await db.execute(
            select(Permission).where(
                Permission.is_active == True,  # noqa: E712
                Permission.is_deleted == False,  # noqa: E712
                Permission.permission_type == 1,  # 只缓存API权限
                Permission.api_path.isnot(None)
            )
        )
        permissions = result.scalars().all()
        
        redis = await RedisClient.get_client()
        # 先删除旧缓存
        await redis.delete(API_PERMISSION_CACHE_KEY)
        
        cache_data = {}
        for perm in permissions:
            if perm.api_path:
                # 存储权限ID，key为 "path:method"
                cache_key = f"{perm.api_path}:{perm.http_method}"
                cache_data[cache_key] = perm.id
                # 如果是ALL方法，也存储到各个具体方法
                if perm.http_method == 5:  # ALL
                    for method_code in [0, 1, 2, 3, 4]:
                        key = f"{perm.api_path}:{method_code}"
                        if key not in cache_data:
                            cache_data[key] = perm.id
        
        if cache_data:
            await redis.hset(API_PERMISSION_CACHE_KEY, mapping=cache_data)
            await redis.expire(API_PERMISSION_CACHE_KEY, API_PERMISSION_CACHE_TTL)
    
    async def clear_cache(self):
        """清除所有权限相关的 Redis 缓存"""
        redis = await RedisClient.get_client()
        # 清除 API 路径映射缓存
        await redis.delete(API_PERMISSION_CACHE_KEY)
        # 清除所有角色权限缓存
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=f"{ROLE_PERMISSION_CACHE_PREFIX}*", count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    
    def _match_path(self, request_path: str, permission_path: str) -> bool:
        """
        匹配请求路径和权限路径
        
        支持路径参数，如 /api/user/{id} 匹配 /api/user/123
        """
        # 将权限路径中的{xxx}替换为正则表达式
        pattern = re.sub(r'\{[^}]+\}', r'[^/]+', permission_path)
        pattern = f'^{pattern}$'
        return bool(re.match(pattern, request_path))
    
    async def find_permission_id(self, request_path: str, http_method: str) -> Optional[str]:
        """
        根据请求路径和方法查找对应的权限ID（从 Redis 缓存查询）
        
        :param request_path: 请求路径，如 /api/core/user
        :param http_method: HTTP方法，如 GET, POST
        :return: 权限ID，如果没有找到则返回None
        """
        method_code = HTTP_METHOD_MAP.get(http_method.upper(), 0)
        redis = await RedisClient.get_client()
        
        # 1. 精确匹配
        cache_key = f"{request_path}:{method_code}"
        perm_id = await redis.hget(API_PERMISSION_CACHE_KEY, cache_key)
        if perm_id:
            return perm_id
        
        # 2. 尝试匹配ALL方法
        cache_key_all = f"{request_path}:5"
        perm_id = await redis.hget(API_PERMISSION_CACHE_KEY, cache_key_all)
        if perm_id:
            return perm_id
        
        # 3. 路径参数匹配（需要获取所有缓存条目）
        all_entries = await redis.hgetall(API_PERMISSION_CACHE_KEY)
        if all_entries:
            for entry_key, entry_perm_id in all_entries.items():
                # entry_key 格式: "path:method"
                # 需要从末尾分离出 method（最后一个冒号后的数字）
                last_colon = entry_key.rfind(':')
                if last_colon == -1:
                    continue
                perm_path = entry_key[:last_colon]
                try:
                    perm_method = int(entry_key[last_colon + 1:])
                except ValueError:
                    continue
                
                if perm_method in (method_code, 5):  # 匹配具体方法或ALL
                    if '{' in perm_path and self._match_path(request_path, perm_path):
                        return entry_perm_id
        
        return None
    
    async def check_permission(
        self,
        db: AsyncSession,
        user_id: str,
        role_id: Optional[str] = None,
        is_superuser: bool = False,
        request_path: str = "",
        http_method: str = "",
        role_ids: Optional[List[str]] = None,
    ) -> tuple[bool, str]:
        """
        检查用户是否有访问指定API的权限（支持多角色）
        
        :param db: 数据库会话
        :param user_id: 用户ID
        :param role_id: 角色ID（单个，向后兼容）
        :param is_superuser: 是否超级管理员
        :param request_path: 请求路径
        :param http_method: HTTP方法
        :param role_ids: 角色ID列表（多个角色）
        :return: (是否有权限, 错误信息)
        """
        # 超级管理员跳过权限检查
        if is_superuser:
            return True, ""
        
        # 确保缓存已加载
        redis = await RedisClient.get_client()
        cache_exists = await redis.exists(API_PERMISSION_CACHE_KEY)
        if not cache_exists:
            await self.load_permissions_cache(db)
        
        # 查找该API对应的权限
        permission_id = await self.find_permission_id(request_path, http_method)
        
        # 如果该API没有配置权限，默认放行
        if not permission_id:
            return True, ""
        
        # 处理角色ID列表
        if role_ids is None:
            role_ids = [role_id] if role_id else []
        
        # 用户没有角色，无权限
        if not role_ids:
            return False, "用户未分配角色，无权访问此接口"
        
        # 检查用户的任一角色是否有该权限（只要有一个角色有权限即可）
        for rid in role_ids:
            has_permission = await self._check_role_has_permission(db, rid, permission_id)
            if has_permission:
                return True, ""
        
        return False, "权限不足，无权访问此接口"
    
    async def _get_role_permission_ids(
        self,
        db: AsyncSession,
        role_id: str,
    ) -> Set[str]:
        """
        获取角色的所有权限ID集合（Redis 缓存）
        """
        redis = await RedisClient.get_client()
        cache_key = f"{ROLE_PERMISSION_CACHE_PREFIX}{role_id}"
        
        # 从 Redis 获取缓存
        cached = await redis.get(cache_key)
        # if cached:
        #     try:
        #         return set(json.loads(cached))
        #     except (json.JSONDecodeError, TypeError):
        #         pass
        
        # 缓存未命中，从数据库加载
        from core.role.model import Role
        
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(
                Role.id == role_id,
                Role.status == True,  # noqa: E712
                Role.is_deleted == False  # noqa: E712
            )
        )
        role = result.scalar_one_or_none()
        
        perm_ids: Set[str] = set()
        if role and role.permissions:
            for perm in role.permissions:
                if perm.is_active:
                    perm_ids.add(perm.id)
        
        # 写入 Redis 缓存
        await redis.set(cache_key, json.dumps(list(perm_ids)), ex=ROLE_PERMISSION_CACHE_TTL)
        return perm_ids

    async def _check_role_has_permission(
        self,
        db: AsyncSession,
        role_id: str,
        permission_id: str
    ) -> bool:
        """
        检查角色是否有指定权限
        """
        perm_ids = await self._get_role_permission_ids(db, role_id)
        return permission_id in perm_ids


# 全局权限检查器实例
api_permission_checker = APIPermissionChecker()


async def check_api_permission(
    db: AsyncSession,
    user_id: str,
    role_id: Optional[str] = None,
    is_superuser: bool = False,
    request_path: str = "",
    http_method: str = "",
    role_ids: Optional[List[str]] = None,
) -> tuple[bool, str]:
    """
    检查API权限的便捷函数（支持多角色）
    
    :return: (是否有权限, 错误信息)
    """
    return await api_permission_checker.check_permission(
        db, user_id, role_id, is_superuser, request_path, http_method, role_ids
    )


async def refresh_permission_cache(db: AsyncSession):
    """
    刷新权限缓存
    
    当权限数据变更时调用此函数
    """
    await api_permission_checker.load_permissions_cache(db)


async def clear_permission_cache():
    """
    清除权限缓存
    """
    await api_permission_checker.clear_cache()


async def clear_role_permission_cache(role_id: str):
    """
    清除指定角色的权限缓存
    
    :param role_id: 角色ID
    """
    redis = await RedisClient.get_client()
    await redis.delete(f"{ROLE_PERMISSION_CACHE_PREFIX}{role_id}")


async def clear_all_role_permission_cache():
    """
    清除所有角色的权限缓存
    """
    redis = await RedisClient.get_client()
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=f"{ROLE_PERMISSION_CACHE_PREFIX}*", count=100)
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


async def get_user_api_permissions(
    db: AsyncSession,
    role_id: Optional[str] = None,
    is_superuser: bool = False,
    role_ids: Optional[List[str]] = None,
) -> Set[str]:
    """
    获取用户的API权限列表（返回API路径集合，支持多角色）
    """
    if is_superuser:
        return {"*"}  # 超级管理员有所有权限
    
    # 处理角色ID列表
    if role_ids is None:
        role_ids = [role_id] if role_id else []
    
    if not role_ids:
        return set()
    
    from core.role.model import Role
    
    api_paths = set()
    
    # 合并所有角色的权限
    for rid in role_ids:
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(
                Role.id == rid,
                Role.status == True,  # noqa: E712
                Role.is_deleted == False  # noqa: E712
            )
        )
        role = result.scalar_one_or_none()
        
        if role and role.permissions:
            for perm in role.permissions:
                if perm.is_active and perm.api_path:
                    api_paths.add(perm.api_path)
    
    return api_paths


async def get_user_permission_codes(
    db: AsyncSession,
    role_id: Optional[str] = None,
    is_superuser: bool = False,
    role_ids: Optional[List[str]] = None,
) -> Set[str]:
    """
    获取用户的权限代码列表（返回权限代码集合，支持多角色）
    """
    if is_superuser:
        return {"*"}  # 超级管理员有所有权限
    
    # 处理角色ID列表
    if role_ids is None:
        role_ids = [role_id] if role_id else []
    
    if not role_ids:
        return set()
    
    from core.role.model import Role
    
    permission_codes = set()
    
    # 合并所有角色的权限
    for rid in role_ids:
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(
                Role.id == rid,
                Role.status == True,  # noqa: E712
                Role.is_deleted == False  # noqa: E712
            )
        )
        role = result.scalar_one_or_none()
        
        if role and role.permissions:
            for perm in role.permissions:
                if perm.is_active and perm.code:
                    permission_codes.add(perm.code)
    
    return permission_codes
