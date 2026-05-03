#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dept Schema - 部门数据验证模式
"""
from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


class DeptBase(BaseModel):
    """部门基础Schema"""
    name: str = Field(..., min_length=1, max_length=64, description="部门名称")
    code: Optional[str] = Field(None, max_length=32, description="部门编码")
    dept_type: str = Field(default="department", description="部门类型")
    phone: Optional[str] = Field(None, max_length=20, description="部门电话")
    email: Optional[str] = Field(None, max_length=64, description="部门邮箱")
    status: bool = Field(default=True, description="部门状态")
    description: Optional[str] = Field(None, description="部门描述")
    parent_id: Optional[str] = Field(None, description="父部门ID")
    lead_id: Optional[str] = Field(None, description="部门领导ID")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证部门编码格式"""
        if v and not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("部门编码只能包含字母、数字、下划线和横线")
        return v
    
    @field_validator("dept_type")
    @classmethod
    def validate_dept_type(cls, v):
        """验证部门类型"""
        valid_types = ["company", "department", "team", "other"]
        if v not in valid_types:
            raise ValueError(f"部门类型必须是以下之一: {', '.join(valid_types)}")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """验证电话格式"""
        if v and not all(c.isdigit() or c in "-+() " for c in v):
            raise ValueError("电话号码格式不正确")
        return v


class DeptCreate(DeptBase):
    """部门创建Schema"""
    pass


class DeptUpdate(BaseModel):
    """部门更新Schema - 所有字段可选"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="部门名称")
    code: Optional[str] = Field(None, max_length=32, description="部门编码")
    dept_type: Optional[str] = Field(None, description="部门类型")
    phone: Optional[str] = Field(None, max_length=20, description="部门电话")
    email: Optional[str] = Field(None, max_length=64, description="部门邮箱")
    status: Optional[bool] = Field(None, description="部门状态")
    description: Optional[str] = Field(None, description="部门描述")
    parent_id: Optional[str] = Field(None, description="父部门ID")
    lead_id: Optional[str] = Field(None, description="部门领导ID")
    sort: Optional[int] = Field(None, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证部门编码格式"""
        if v is not None and v and not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("部门编码只能包含字母、数字、下划线和横线")
        return v
    
    @field_validator("dept_type")
    @classmethod
    def validate_dept_type(cls, v):
        """验证部门类型"""
        if v is not None:
            valid_types = ["company", "department", "team", "other"]
            if v not in valid_types:
                raise ValueError(f"部门类型必须是以下之一: {', '.join(valid_types)}")
        return v
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        """验证电话格式"""
        if v is not None and v and not all(c.isdigit() or c in "-+() " for c in v):
            raise ValueError("电话号码格式不正确")
        return v


class DeptResponse(BaseModel):
    """部门响应Schema"""
    id: str
    name: str
    code: Optional[str] = None
    dept_type: str
    dept_type_display: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: bool
    description: Optional[str] = None
    parent_id: Optional[str] = None
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    level: int = 0
    path: Optional[str] = None
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeptTreeNode(BaseModel):
    """部门树形节点"""
    id: str
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    dept_type: str
    status: bool
    level: int
    sort: int = 0
    children: List["DeptTreeNode"] = []
    
    model_config = ConfigDict(from_attributes=True)


class DeptSimple(BaseModel):
    """部门简单输出（用于选择器）"""
    id: str
    name: str
    code: Optional[str] = None
    parent_id: Optional[str] = None
    level: int
    status: bool
    
    model_config = ConfigDict(from_attributes=True)


class DeptBatchDeleteIn(BaseModel):
    """批量删除部门输入"""
    ids: List[str] = Field(..., description="要删除的部门ID列表")


class DeptBatchDeleteOut(BaseModel):
    """批量删除部门输出"""
    count: int = Field(..., description="删除的记录数")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class DeptBatchUpdateStatusIn(BaseModel):
    """批量更新部门状态输入"""
    ids: List[str] = Field(..., description="部门ID列表")
    status: bool = Field(..., description="部门状态")


class DeptBatchUpdateStatusOut(BaseModel):
    """批量更新部门状态输出"""
    count: int = Field(..., description="更新的记录数")


class DeptPathOut(BaseModel):
    """部门路径响应"""
    dept_id: str = Field(..., description="部门ID")
    dept_name: str = Field(..., description="部门名称")
    path: List[DeptSimple] = Field(..., description="从根到当前部门的路径")


class DeptUserSchema(BaseModel):
    """部门用户Schema"""
    id: str
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    dept_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DeptUserIn(BaseModel):
    """部门用户输入"""
    user_id: Optional[str] = Field(None, description="单个用户ID")
    user_ids: List[str] = Field(default=[], description="用户ID列表")


class DeptStatsResponse(BaseModel):
    """部门统计响应"""
    total_count: int = Field(..., description="总部门数")
    active_count: int = Field(..., description="启用部门数")
    inactive_count: int = Field(..., description="禁用部门数")
    root_count: int = Field(..., description="根部门数")
    type_stats: Dict[str, int] = Field(..., description="按类型统计")
    max_level: int = Field(..., description="最大层级")


class DeptMoveRequest(BaseModel):
    """移动部门请求"""
    dept_id: str = Field(..., description="要移动的部门ID")
    new_parent_id: Optional[str] = Field(None, description="新父部门ID，为空表示移动到根节点")


class DeptSearchRequest(BaseModel):
    """搜索部门请求"""
    keyword: str = Field(..., description="搜索关键词")
