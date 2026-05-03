#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据权限工具函数

提供独立的数据权限过滤功能，供不继承 BaseService 的模块使用
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from utils.context import get_current_user_info_from_context


async def get_data_scope_filter(
    db: AsyncSession,
    resource_type: str,
    user_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    获取数据权限过滤条件
    
    :param db: 数据库会话
    :param resource_type: 资源类型（如 "page", "data_source" 等）
    :param user_info: 用户信息字典，如果不传则自动从上下文获取
    :return: 数据权限过滤条件字典
    """
    # 如果没有传入用户信息，从上下文获取
    if user_info is None:
        user_info = get_current_user_info_from_context()
    
    # 如果没有用户信息，返回全部数据
    if not user_info:
        return {
            'filter_type': 'all',
            'scope': 0,
            'user_id': None,
            'dept_id': None,
            'dept_ids': None
        }
    
    # 超级管理员：全部数据
    if user_info.get("is_superuser", False):
        return {
            'filter_type': 'all',
            'scope': 0,
            'user_id': None,
            'dept_id': None,
            'dept_ids': None
        }
    
    # 如果没有定义资源类型，默认全部数据
    if not resource_type:
        return {
            'filter_type': 'all',
            'scope': 0,
            'user_id': None,
            'dept_id': None,
            'dept_ids': None
        }
    
    # 使用资源类型绑定的数据权限
    from core.resource_scope.scope_permission.service import ResourceDataScopeConfigService
    
    # 查询资源数据权限配置（支持多角色）
    config_dict = await ResourceDataScopeConfigService.get_resource_data_scope(
        db=db,
        role_ids=user_info.get("role_ids", []),
        resource_type=resource_type,
        is_superuser=user_info.get("is_superuser", False)
    )
    
    # 填充用户和部门信息
    if config_dict['filter_type'] == 'self':
        config_dict['user_id'] = user_info.get("user_id")
    elif config_dict['filter_type'] == 'dept':
        config_dict['dept_id'] = user_info.get("dept_id")
    elif config_dict['filter_type'] == 'dept_and_children':
        # 获取部门树
        if user_info.get("dept_id"):
            from core.auth.dept.service import DeptService
            dept_ids = await DeptService.get_dept_and_children_ids(db, user_info.get("dept_id"))
            config_dict['dept_ids'] = dept_ids
        else:
            config_dict['dept_ids'] = []
    
    return config_dict


def apply_data_scope_to_conditions(
    model,
    data_scope_filter: Dict[str, Any],
    dept_field: str = "sys_dept_id",
    user_field: str = "sys_creator_id"
) -> List[Any]:
    """
    根据数据权限过滤条件生成 SQLAlchemy 条件列表
    
    注意：当 sys_creator_id 或 sys_dept_id 为空时，记录对所有人可见
    
    :param model: SQLAlchemy 模型类
    :param data_scope_filter: 数据权限过滤条件
    :param dept_field: 部门字段名
    :param user_field: 用户字段名
    :return: SQLAlchemy 条件列表
    """
    conditions = []
    filter_type = data_scope_filter.get('filter_type')
    
    # 全部数据：不添加过滤条件
    if filter_type == 'all':
        return conditions
    
    # 仅本人数据：匹配创建人 OR 创建人为空（对所有人可见）
    if filter_type == 'self':
        if hasattr(model, user_field):
            user_field_obj = getattr(model, user_field)
            conditions.append(
                or_(
                    user_field_obj == data_scope_filter['user_id'],
                    user_field_obj.is_(None)  # 创建人为空时所有人可见
                )
            )
        return conditions
    
    # 本部门数据：匹配部门 OR 部门为空（对所有人可见）
    if filter_type == 'dept':
        if hasattr(model, dept_field):
            dept_field_obj = getattr(model, dept_field)
            conditions.append(
                or_(
                    dept_field_obj == data_scope_filter['dept_id'],
                    dept_field_obj.is_(None)  # 部门为空时所有人可见
                )
            )
        return conditions
    
    # 本部门及下级部门数据 / 自定义数据
    if filter_type in ('dept_and_children', 'custom'):
        if hasattr(model, dept_field):
            dept_field_obj = getattr(model, dept_field)
            dept_ids = data_scope_filter.get('dept_ids', [])
            if dept_ids:
                conditions.append(
                    or_(
                        dept_field_obj.in_(dept_ids),
                        dept_field_obj.is_(None)  # 部门为空时所有人可见
                    )
                )
            else:
                # 如果没有部门ID，只返回部门为空的记录
                conditions.append(dept_field_obj.is_(None))
        return conditions
    
    return conditions
