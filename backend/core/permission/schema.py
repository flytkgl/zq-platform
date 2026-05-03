#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Permission Schema - 权限数据验证模式
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


class PermissionBase(BaseModel):
    """权限基础Schema"""
    menu_id: str = Field(..., description="菜单ID")
    name: str = Field(..., min_length=1, max_length=64, description="权限名称")
    code: str = Field(..., min_length=1, max_length=64, description="权限编码")
    permission_type: int = Field(default=0, description="权限类型（0-按钮权限, 1-API权限, 3-其他权限）")
    api_path: Optional[str] = Field(None, max_length=200, description="API路径")
    http_method: int = Field(default=0, description="HTTP方法（0-GET, 1-POST, 2-PUT, 3-DELETE, 4-PATCH, 5-ALL）")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: bool = Field(default=True, description="是否启用")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证权限编码格式"""
        if not v:
            raise ValueError("权限编码不能为空")
        if not all(c.isalnum() or c in '_:' for c in v):
            raise ValueError("权限编码只能包含字母、数字、下划线和冒号")
        return v
    
    @field_validator("http_method")
    @classmethod
    def validate_http_method(cls, v):
        """验证HTTP方法"""
        if v not in [0, 1, 2, 3, 4, 5]:
            raise ValueError("HTTP方法必须在 0-5 之间")
        return v
    
    @field_validator("permission_type")
    @classmethod
    def validate_permission_type(cls, v):
        """验证权限类型"""
        if v not in [0, 1, 3]:
            raise ValueError("权限类型必须在 0, 1, 3 之间")
        return v


class PermissionCreate(PermissionBase):
    """权限创建Schema"""
    pass


class PermissionUpdate(BaseModel):
    """权限更新Schema - 所有字段可选"""
    menu_id: Optional[str] = Field(None, description="菜单ID")
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="权限名称")
    code: Optional[str] = Field(None, min_length=1, max_length=64, description="权限编码")
    permission_type: Optional[int] = Field(None, description="权限类型")
    api_path: Optional[str] = Field(None, max_length=200, description="API路径")
    http_method: Optional[int] = Field(None, description="HTTP方法")
    description: Optional[str] = Field(None, description="权限描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort: Optional[int] = Field(None, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证权限编码格式"""
        if v is not None:
            if not v:
                raise ValueError("权限编码不能为空")
            if not all(c.isalnum() or c in '_:' for c in v):
                raise ValueError("权限编码只能包含字母、数字、下划线和冒号")
        return v
    
    @field_validator("http_method")
    @classmethod
    def validate_http_method(cls, v):
        """验证HTTP方法"""
        if v is not None and v not in [0, 1, 2, 3, 4, 5]:
            raise ValueError("HTTP方法必须在 0-5 之间")
        return v
    
    @field_validator("permission_type")
    @classmethod
    def validate_permission_type(cls, v):
        """验证权限类型"""
        if v is not None and v not in [0, 1, 3]:
            raise ValueError("权限类型必须在 0, 1, 3 之间")
        return v


class PermissionResponse(BaseModel):
    """权限响应Schema"""
    id: str
    menu_id: str
    menu_name: Optional[str] = None
    name: str
    code: str
    permission_type: int
    permission_type_display: Optional[str] = None
    api_path: Optional[str] = None
    http_method: int
    http_method_display: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PermissionSimple(BaseModel):
    """权限简单输出"""
    id: str
    name: str
    code: str
    permission_type: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class PermissionBatchDeleteIn(BaseModel):
    """批量删除权限输入"""
    ids: List[str] = Field(..., description="要删除的权限ID列表")


class PermissionBatchDeleteOut(BaseModel):
    """批量删除权限输出"""
    count: int = Field(..., description="删除的记录数")


class PermissionBatchUpdateStatusIn(BaseModel):
    """批量更新权限状态输入"""
    ids: List[str] = Field(..., description="权限ID列表")
    is_active: bool = Field(..., description="是否启用")


class PermissionBatchUpdateStatusOut(BaseModel):
    """批量更新权限状态输出"""
    count: int = Field(..., description="更新的记录数")


class PermissionSearchRequest(BaseModel):
    """搜索权限请求"""
    keyword: str = Field(..., description="搜索关键词")


class PermissionRouteItem(BaseModel):
    """单个路由权限项"""
    path: str = Field(..., description="API路径")
    method: str = Field(..., description="HTTP方法")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限编码")
    summary: Optional[str] = Field(None, description="权限描述")
    permission_type: int = Field(default=1, description="权限类型")
    http_method: int = Field(..., description="HTTP方法编码")
    is_active: bool = Field(default=True, description="是否启用")


class PermissionBatchCreateFromRoutesIn(BaseModel):
    """从路由批量创建权限输入"""
    menu_id: str = Field(..., description="菜单ID")
    routes: List[PermissionRouteItem] = Field(..., description="要创建的权限列表")


class PermissionBatchCreateFromRoutesOut(BaseModel):
    """从路由批量创建权限输出"""
    created: int = Field(..., description="创建的权限数")
    skipped: int = Field(..., description="跳过的权限数")
    failed: int = Field(..., description="失败的权限数")
    errors: List[str] = Field(default=[], description="错误信息列表")
