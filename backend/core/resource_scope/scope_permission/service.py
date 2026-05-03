#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ResourceDataScopeConfig Service - 资源数据权限配置服务
"""
from typing import List, Optional, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.resource_scope.scope_permission.model import ResourceDataScopeConfig
from core.resource_scope.scope_permission.schema import (
    ResourceDataScopeConfigCreate,
    ResourceDataScopeConfigUpdate,
    RoleResourceScopeBatchUpdate
)


class ResourceDataScopeConfigService(BaseService[
    ResourceDataScopeConfig,
    ResourceDataScopeConfigCreate,
    ResourceDataScopeConfigUpdate
]):
    """资源数据权限配置服务"""
    
    model = ResourceDataScopeConfig
    
    @classmethod
    async def get_by_role_and_resource(
        cls,
        db: AsyncSession,
        role_id: str,
        resource_type: str
    ) -> Optional[ResourceDataScopeConfig]:
        """
        根据角色ID和资源类型获取配置
        
        :param db: 数据库会话
        :param role_id: 角色ID
        :param resource_type: 资源类型
        :return: 配置记录或None
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.role_id == role_id,
                cls.model.resource_type == resource_type,
                cls.model.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_role_configs(
        cls,
        db: AsyncSession,
        role_id: str
    ) -> List[ResourceDataScopeConfig]:
        """
        获取角色的所有资源权限配置
        
        :param db: 数据库会话
        :param role_id: 角色ID
        :return: 配置列表
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.role_id == role_id,
                cls.model.is_deleted == False  # noqa: E712
            )
        )
        return list(result.scalars().all())
    
    @classmethod
    async def batch_update_role_configs(
        cls,
        db: AsyncSession,
        data: RoleResourceScopeBatchUpdate
    ) -> List[ResourceDataScopeConfig]:
        """
        批量更新角色的资源权限配置
        
        :param db: 数据库会话
        :param data: 批量更新数据
        :return: 更新后的配置列表
        """
        # 删除该角色的所有现有配置
        await db.execute(
            delete(cls.model).where(cls.model.role_id == data.role_id)
        )
        
        # 创建新配置
        configs = []
        for config_data in data.configs:
            config = cls.model(
                role_id=data.role_id,
                resource_type=config_data.resource_type,
                data_scope=config_data.data_scope,
                dept_ids=config_data.dept_ids
            )
            db.add(config)
            configs.append(config)
        
        await db.commit()
        
        # 刷新所有配置
        for config in configs:
            await db.refresh(config)
        
        return configs
    
    @classmethod
    def _merge_data_scope_configs(cls, configs: List[ResourceDataScopeConfig]) -> ResourceDataScopeConfig:
        """
        合并多个角色的数据权限配置（使用最宽松策略）
        
        权限优先级：0(全部) > 4(自定义) > 3(本部门及下级) > 2(本部门) > 1(仅本人)
        
        :param configs: 配置列表
        :return: 合并后的配置
        """
        if not configs:
            # 返回默认配置
            return ResourceDataScopeConfig(data_scope=0)
        
        # 如果有任何一个角色是"全部数据"，则返回全部数据
        for config in configs:
            if config.data_scope == 0:
                return config
        
        # 找出最宽松的权限
        max_scope = max(config.data_scope for config in configs)
        
        # 如果是自定义权限，合并所有自定义部门
        if max_scope == 4:
            all_dept_ids = set()
            for config in configs:
                if config.data_scope == 4 and config.dept_ids:
                    all_dept_ids.update(config.dept_ids)
            
            # 创建合并后的配置
            merged = ResourceDataScopeConfig(
                data_scope=4,
                dept_ids=list(all_dept_ids) if all_dept_ids else []
            )
            return merged
        
        # 返回最宽松的配置
        for config in configs:
            if config.data_scope == max_scope:
                return config
        
        return configs[0]
    
    @classmethod
    async def get_resource_data_scope(
        cls,
        db: AsyncSession,
        role_id: Optional[str] = None,
        resource_type: str = None,
        is_superuser: bool = False,
        role_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取资源的数据权限配置（支持多角色）
        
        :param db: 数据库会话
        :param role_id: 角色ID（单个，向后兼容）
        :param resource_type: 资源类型
        :param is_superuser: 是否超级管理员
        :param role_ids: 角色ID列表（多个角色）
        :return: 数据权限配置字典
        """
        # 超级管理员：全部数据
        if is_superuser:
            return {
                'filter_type': 'all',
                'scope': 0,
                'user_id': None,
                'dept_id': None,
                'dept_ids': None
            }
        
        # 处理角色ID列表
        if role_ids is None:
            role_ids = [role_id] if role_id else []
        
        # 没有角色：仅本人
        if not role_ids:
            return {
                'filter_type': 'self',
                'scope': 1,
                'user_id': None,  # 将在应用时填充
                'dept_id': None,
                'dept_ids': None
            }
        
        # 查询所有角色的配置
        configs = []
        for rid in role_ids:
            config = await cls.get_by_role_and_resource(db, rid, resource_type)
            if config:
                configs.append(config)
        
        # 如果没有配置，默认全部数据
        if not configs:
            return {
                'filter_type': 'all',
                'scope': 0,
                'user_id': None,
                'dept_id': None,
                'dept_ids': None
            }
        
        # 合并多个角色的权限配置（使用最宽松策略）
        # 权限优先级：0(全部) > 4(自定义) > 3(本部门及下级) > 2(本部门) > 1(仅本人)
        merged_config = cls._merge_data_scope_configs(configs)
        
        # 根据 data_scope 返回配置
        if merged_config.data_scope == 0:  # 全部数据
            return {
                'filter_type': 'all',
                'scope': 0,
                'user_id': None,
                'dept_id': None,
                'dept_ids': None
            }
        elif merged_config.data_scope == 1:  # 仅本人
            return {
                'filter_type': 'self',
                'scope': 1,
                'user_id': None,  # 将在应用时填充
                'dept_id': None,
                'dept_ids': None
            }
        elif merged_config.data_scope == 2:  # 本部门
            return {
                'filter_type': 'dept',
                'scope': 2,
                'user_id': None,
                'dept_id': None,  # 将在应用时填充
                'dept_ids': None
            }
        elif merged_config.data_scope == 3:  # 本部门及下级
            return {
                'filter_type': 'dept_and_children',
                'scope': 3,
                'user_id': None,
                'dept_id': None,
                'dept_ids': None  # 将在应用时填充
            }
        elif merged_config.data_scope == 4:  # 自定义
            return {
                'filter_type': 'custom',
                'scope': 4,
                'user_id': None,
                'dept_id': None,
                'dept_ids': merged_config.dept_ids or []
            }
        
        # 默认全部数据
        return {
            'filter_type': 'all',
            'scope': 0,
            'user_id': None,
            'dept_id': None,
            'dept_ids': None
        }
