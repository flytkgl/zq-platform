#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Role Schema - 角色数据验证模式
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


class RoleBase(BaseModel):
    """角色基础Schema"""
    name: str = Field(..., min_length=1, max_length=64, description="角色名称")
    code: str = Field(..., min_length=1, max_length=64, description="角色编码")
    role_type: int = Field(default=1, description="角色类型（0-系统角色, 1-自定义角色）")
    status: bool = Field(default=True, description="角色状态")
    priority: int = Field(default=0, description="角色优先级")
    description: Optional[str] = Field(None, description="角色描述")
    remark: Optional[str] = Field(None, description="备注")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证角色编码格式"""
        if not v:
            raise ValueError("角色编码不能为空")
        if not v.replace('_', '').isalnum():
            raise ValueError("角色编码只能包含字母、数字和下划线")
        return v
    
    @field_validator("role_type")
    @classmethod
    def validate_role_type(cls, v):
        """验证角色类型"""
        if v not in [0, 1]:
            raise ValueError("角色类型必须为 0(系统角色) 或 1(自定义角色)")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """验证优先级"""
        if v < 0:
            raise ValueError("优先级不能为负数")
        return v


class RoleCreate(RoleBase):
    """角色创建Schema"""
    menu_ids: List[str] = Field(default=[], description="菜单ID列表")
    permission_ids: List[str] = Field(default=[], description="权限ID列表")
    dept_ids: List[str] = Field(default=[], description="部门ID列表")


class RoleUpdate(BaseModel):
    """角色更新Schema - 所有字段可选"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="角色名称")
    code: Optional[str] = Field(None, min_length=1, max_length=64, description="角色编码")
    role_type: Optional[int] = Field(None, description="角色类型")
    status: Optional[bool] = Field(None, description="角色状态")
    priority: Optional[int] = Field(None, description="角色优先级")
    description: Optional[str] = Field(None, description="角色描述")
    remark: Optional[str] = Field(None, description="备注")
    sort: Optional[int] = Field(None, description="排序")
    menu_ids: Optional[List[str]] = Field(None, description="菜单ID列表")
    permission_ids: Optional[List[str]] = Field(None, description="权限ID列表")
    dept_ids: Optional[List[str]] = Field(None, description="部门ID列表")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证角色编码格式"""
        if v is not None:
            if not v:
                raise ValueError("角色编码不能为空")
            if not v.replace('_', '').isalnum():
                raise ValueError("角色编码只能包含字母、数字和下划线")
        return v
    
    @field_validator("role_type")
    @classmethod
    def validate_role_type(cls, v):
        """验证角色类型"""
        if v is not None and v not in [0, 1]:
            raise ValueError("角色类型必须为 0(系统角色) 或 1(自定义角色)")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """验证优先级"""
        if v is not None and v < 0:
            raise ValueError("优先级不能为负数")
        return v


class RoleResponse(BaseModel):
    """角色响应Schema"""
    id: str
    name: str
    code: str
    role_type: int
    role_type_display: Optional[str] = None
    status: bool
    priority: int
    description: Optional[str] = None
    remark: Optional[str] = None
    user_count: int = 0
    menu_count: int = 0
    permission_count: int = 0
    can_delete: bool = True
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleDetail(RoleResponse):
    """角色详情响应Schema（包含关联数据）"""
    menu_ids: List[str] = []
    permission_ids: List[str] = []
    dept_ids: List[str] = []


class RoleSimple(BaseModel):
    """角色简单输出（用于选择器）"""
    id: str
    name: str
    code: str
    status: bool
    role_type: int
    
    model_config = ConfigDict(from_attributes=True)


class RoleBatchDeleteIn(BaseModel):
    """批量删除角色输入"""
    ids: List[str] = Field(..., description="要删除的角色ID列表")


class RoleBatchDeleteOut(BaseModel):
    """批量删除角色输出"""
    count: int = Field(..., description="删除的记录数")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class RoleBatchUpdateStatusIn(BaseModel):
    """批量更新角色状态输入"""
    ids: List[str] = Field(..., description="角色ID列表")
    status: bool = Field(..., description="角色状态")


class RoleBatchUpdateStatusOut(BaseModel):
    """批量更新角色状态输出"""
    count: int = Field(..., description="更新的记录数")


class RoleUserSchema(BaseModel):
    """角色关联的用户信息"""
    id: str
    name: Optional[str] = None
    username: str
    avatar: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    dept_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RoleUserIn(BaseModel):
    """角色用户操作输入"""
    role_id: str = Field(..., description="角色ID")
    user_ids: List[str] = Field(default=[], description="用户ID列表")
    user_id: Optional[str] = Field(None, description="单个用户ID")


class RoleMenuPermissionUpdateIn(BaseModel):
    """更新角色菜单和权限输入"""
    menu_ids: List[str] = Field(default=[], description="菜单ID列表")
    permission_ids: List[str] = Field(default=[], description="权限ID列表")


class RoleSearchRequest(BaseModel):
    """搜索角色请求"""
    keyword: str = Field(..., description="搜索关键词")


class RoleCopyRequest(BaseModel):
    """复制角色请求"""
    new_name: str = Field(..., description="新角色名称")
    new_code: str = Field(..., description="新角色编码")
