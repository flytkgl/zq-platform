#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ResourceDataScopeConfig Schema - 资源数据权限配置Schema
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.base_schema import CSTDatetime


class ResourceDataScopeConfigBase(BaseModel):
    """资源数据权限配置基础Schema"""
    role_id: str = Field(..., description="角色ID")
    resource_type: str = Field(..., description="资源类型")
    data_scope: int = Field(default=0, ge=0, le=4, description="数据权限范围（0-4）")
    dept_ids: Optional[List[str]] = Field(default=None, description="自定义权限的部门ID列表")


class ResourceDataScopeConfigCreate(ResourceDataScopeConfigBase):
    """创建资源数据权限配置Schema"""
    pass


class ResourceDataScopeConfigUpdate(BaseModel):
    """更新资源数据权限配置Schema"""
    data_scope: Optional[int] = Field(default=None, ge=0, le=4, description="数据权限范围")
    dept_ids: Optional[List[str]] = Field(default=None, description="部门ID列表")


class ResourceDataScopeConfigResponse(ResourceDataScopeConfigBase):
    """资源数据权限配置响应Schema"""
    id: str
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoleResourceScopeConfig(BaseModel):
    """角色的资源权限配置（用于批量配置）"""
    resource_type: str = Field(..., description="资源类型")
    data_scope: int = Field(default=0, ge=0, le=4, description="数据权限范围")
    dept_ids: Optional[List[str]] = Field(default=None, description="部门ID列表")


class RoleResourceScopeBatchUpdate(BaseModel):
    """批量更新角色的资源权限配置"""
    role_id: str = Field(..., description="角色ID")
    configs: List[RoleResourceScopeConfig] = Field(..., description="资源权限配置列表")
