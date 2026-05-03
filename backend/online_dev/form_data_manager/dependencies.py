#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单数据权限校验依赖
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)


async def get_user_info(request: Request) -> Dict[str, Any]:
    """从请求中获取用户信息"""
    return {
        "user_id": getattr(request.state, 'user_id', None),
        "dept_id": getattr(request.state, 'dept_id', None),
        "role_ids": getattr(request.state, 'role_ids', []),
        "is_superuser": getattr(request.state, 'is_superuser', False),
    }


async def check_form_permission(
    form_code: str,
    action: str,
    request: Request,
    db: AsyncSession
) -> bool:
    """
    检查用户是否有表单操作权限
    
    :param form_code: 表单编码
    :param action: 操作类型 (view/add/edit/delete/export/import)
    :param request: 请求对象
    :param db: 数据库会话
    :return: True 表示有权限
    :raises HTTPException: 无权限时抛出 403 异常
    """
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    # 超级管理员跳过权限检查
    if is_superuser:
        return True
    
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 权限编码
    perm_code = f"form:{form_code}:{action}"
    
    # 查询用户角色的权限
    from core.user.model import User
    from core.role.model import Role, role_permission
    from core.permission.model import Permission
    
    # 获取用户的角色ID列表
    role_ids = getattr(request.state, 'role_ids', [])
    
    if not role_ids:
        # 如果 request.state 中没有角色信息，从数据库查询
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        role_ids = [role.id for role in user.roles] if hasattr(user, 'roles') else []
    
    if not role_ids:
        raise HTTPException(status_code=403, detail=f"没有{action}权限")
    
    # 查询角色是否有该权限
    perm_stmt = select(Permission).join(
        role_permission,
        Permission.id == role_permission.c.permission_id
    ).where(
        role_permission.c.role_id.in_(role_ids),
        Permission.code == perm_code,
        Permission.is_active == True,
        Permission.is_deleted == False
    )
    
    perm_result = await db.execute(perm_stmt)
    permission = perm_result.scalar_one_or_none()
    
    if permission:
        return True
    
    # 操作名称映射
    action_names = {
        "view": "查看",
        "add": "新增",
        "edit": "编辑",
        "delete": "删除",
        "export": "导出",
        "import": "导入",
    }
    action_name = action_names.get(action, action)
    
    raise HTTPException(status_code=403, detail=f"没有{action_name}权限")


async def get_user_form_permissions(
    form_code: str,
    request: Request,
    db: AsyncSession
) -> Dict[str, bool]:
    """
    获取用户对表单的所有操作权限
    
    :param form_code: 表单编码
    :param request: 请求对象
    :param db: 数据库会话
    :return: 权限字典
    """
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    # 默认权限
    permissions = {
        "view": False,
        "add": False,
        "edit": False,
        "delete": False,
        "export": False,
        "import": False,
    }
    
    # 超级管理员拥有所有权限
    if is_superuser:
        return {k: True for k in permissions.keys()}
    
    if not user_id:
        return permissions
    
    # 获取用户角色ID列表
    role_ids = getattr(request.state, 'role_ids', [])
    
    if not role_ids:
        from core.user.model import User
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if user and hasattr(user, 'roles'):
            role_ids = [role.id for role in user.roles]
    
    if not role_ids:
        return permissions
    
    # 查询用户拥有的表单权限
    from core.role.model import role_permission
    from core.permission.model import Permission
    
    perm_stmt = select(Permission.code).join(
        role_permission,
        Permission.id == role_permission.c.permission_id
    ).where(
        role_permission.c.role_id.in_(role_ids),
        Permission.code.like(f"form:{form_code}:%"),
        Permission.is_active == True,
        Permission.is_deleted == False
    )
    
    perm_result = await db.execute(perm_stmt)
    perm_codes = [row[0] for row in perm_result.fetchall()]
    
    # 解析权限
    for perm_code in perm_codes:
        # 格式: form:{form_code}:{action}
        parts = perm_code.split(":")
        if len(parts) == 3 and parts[2] in permissions:
            permissions[parts[2]] = True
    
    return permissions


async def get_data_scope_filter(
    form_code: str,
    request: Request,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    获取数据权限过滤条件
    
    :param form_code: 表单编码
    :param request: 请求对象
    :param db: 数据库会话
    :return: 数据权限过滤配置
    """
    user_id = getattr(request.state, 'user_id', None)
    dept_id = getattr(request.state, 'dept_id', None)
    role_ids = getattr(request.state, 'role_ids', [])
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    # 超级管理员：全部数据
    if is_superuser:
        return {
            'filter_type': 'all',
            'scope': 0,
            'user_id': None,
            'dept_id': None,
            'dept_ids': None
        }
    
    # 资源类型
    resource_type = f"form:{form_code}"
    
    # 查询数据权限配置
    from core.resource_scope.scope_permission.service import ResourceDataScopeConfigService
    
    config = await ResourceDataScopeConfigService.get_resource_data_scope(
        db=db,
        role_ids=role_ids,
        resource_type=resource_type,
        is_superuser=False
    )
    
    # 填充用户信息
    if config['filter_type'] == 'self':
        config['user_id'] = user_id
    elif config['filter_type'] == 'dept':
        config['dept_id'] = dept_id
    elif config['filter_type'] == 'dept_and_children':
        if dept_id:
            from core.dept.service import DeptService
            descendants = await DeptService.get_descendants(db, dept_id)
            config['dept_ids'] = [dept_id] + [d.id for d in descendants]
        else:
            config['dept_ids'] = []
    
    return config
