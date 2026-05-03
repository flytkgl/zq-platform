#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ResourceDataScopeConfig API - 资源数据权限配置API
"""
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import ResponseModel
from core.resource_scope.scope_permission.schema import (
    ResourceDataScopeConfigCreate,
    ResourceDataScopeConfigUpdate,
    ResourceDataScopeConfigResponse,
    RoleResourceScopeBatchUpdate
)
from core.resource_scope.scope_permission.service import ResourceDataScopeConfigService
from app.resource_registry import ResourceRegistry

router = APIRouter(prefix="/resource-scope", tags=["资源数据权限配置"])


@router.get("/types", response_model=List[Dict], summary="获取所有资源类型")
async def get_resource_types(
    application_id: Optional[str] = Query(None, alias="applicationId", description="应用ID，子应用访问时只显示该应用的资源")
):
    """
    获取所有已注册的资源类型
    
    返回格式：
    [
        {
            "resource_type": "customer",
            "display_name": "客户",
            "model_name": "Customer",
            "table_name": "core_customer"
        },
        ...
    ]
    """
    return ResourceRegistry.get_all_resources(application_id=application_id)


@router.get("/types/list", response_model=List[str], summary="获取资源类型列表")
async def get_resource_type_list():
    """获取所有资源类型的简单列表（只返回 resource_type 字符串）"""
    return ResourceRegistry.get_all_resource_types()


@router.get("/registry/info", response_model=ResponseModel, summary="获取注册表信息")
async def get_registry_info():
    """获取资源类型注册表的统计信息"""
    info = ResourceRegistry.get_registry_info()
    return ResponseModel(message="获取成功", data=info)


@router.post("/", response_model=ResourceDataScopeConfigResponse, summary="创建资源权限配置")
async def create_config(
    data: ResourceDataScopeConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建资源数据权限配置"""
    # 检查是否已存在
    existing = await ResourceDataScopeConfigService.get_by_role_and_resource(
        db, data.role_id, data.resource_type
    )
    if existing:
        raise HTTPException(status_code=400, detail="该角色的资源权限配置已存在")
    
    return await ResourceDataScopeConfigService.create(db=db, data=data)


@router.get("/role/{role_id}", response_model=List[ResourceDataScopeConfigResponse], summary="获取角色的资源权限配置")
async def get_role_configs(
    role_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取角色的所有资源权限配置"""
    return await ResourceDataScopeConfigService.get_role_configs(db, role_id)


@router.put("/role/batch", response_model=List[ResourceDataScopeConfigResponse], summary="批量更新角色的资源权限配置")
async def batch_update_role_configs(
    data: RoleResourceScopeBatchUpdate,
    db: AsyncSession = Depends(get_db)
):
    """批量更新角色的资源权限配置（会删除旧配置，创建新配置）"""
    return await ResourceDataScopeConfigService.batch_update_role_configs(db, data)


@router.get("/{config_id}", response_model=ResourceDataScopeConfigResponse, summary="获取配置详情")
async def get_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取资源权限配置详情"""
    config = await ResourceDataScopeConfigService.get_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.put("/{config_id}", response_model=ResourceDataScopeConfigResponse, summary="更新配置")
async def update_config(
    config_id: str,
    data: ResourceDataScopeConfigUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新资源权限配置"""
    result = await ResourceDataScopeConfigService.update(db, config_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="配置不存在")
    return result


@router.delete("/{config_id}", response_model=ResponseModel, summary="删除配置")
async def delete_config(
    config_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除资源权限配置"""
    success = await ResourceDataScopeConfigService.delete(db, config_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ResponseModel(message="删除成功")
