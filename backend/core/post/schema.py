#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post Schema - 岗位数据验证模式
"""
from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


class PostBase(BaseModel):
    """岗位基础Schema"""
    name: str = Field(..., min_length=1, max_length=64, description="岗位名称")
    code: str = Field(..., min_length=1, max_length=32, description="岗位编码")
    post_type: int = Field(default=4, description="岗位类型（0-管理岗, 1-技术岗, 2-业务岗, 3-职能岗, 4-其他）")
    post_level: int = Field(default=3, description="岗位级别（0-高层, 1-中层, 2-基层, 3-一般员工）")
    status: bool = Field(default=True, description="岗位状态")
    description: Optional[str] = Field(None, description="岗位描述")
    dept_id: Optional[str] = Field(None, description="所属部门ID")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证岗位编码格式"""
        if not v:
            raise ValueError("岗位编码不能为空")
        if not all(c.isalnum() or c in '_-' for c in v):
            raise ValueError("岗位编码只能包含字母、数字、下划线和横线")
        return v
    
    @field_validator("post_type")
    @classmethod
    def validate_post_type(cls, v):
        """验证岗位类型"""
        if v is not None and v not in [0, 1, 2, 3, 4]:
            raise ValueError("岗位类型必须在 0-4 之间")
        return v
    
    @field_validator("post_level")
    @classmethod
    def validate_post_level(cls, v):
        """验证岗位级别"""
        if v is not None and v not in [0, 1, 2, 3]:
            raise ValueError("岗位级别必须在 0-3 之间")
        return v


class PostCreate(PostBase):
    """岗位创建Schema"""
    pass


class PostUpdate(BaseModel):
    """岗位更新Schema - 所有字段可选"""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="岗位名称")
    code: Optional[str] = Field(None, min_length=1, max_length=32, description="岗位编码")
    post_type: Optional[int] = Field(None, description="岗位类型")
    post_level: Optional[int] = Field(None, description="岗位级别")
    status: Optional[bool] = Field(None, description="岗位状态")
    description: Optional[str] = Field(None, description="岗位描述")
    dept_id: Optional[str] = Field(None, description="所属部门ID")
    sort: Optional[int] = Field(None, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证岗位编码格式"""
        if v is not None:
            if not v:
                raise ValueError("岗位编码不能为空")
            if not all(c.isalnum() or c in '_-' for c in v):
                raise ValueError("岗位编码只能包含字母、数字、下划线和横线")
        return v
    
    @field_validator("post_type")
    @classmethod
    def validate_post_type(cls, v):
        """验证岗位类型"""
        if v is not None and v not in [0, 1, 2, 3, 4]:
            raise ValueError("岗位类型必须在 0-4 之间")
        return v
    
    @field_validator("post_level")
    @classmethod
    def validate_post_level(cls, v):
        """验证岗位级别"""
        if v is not None and v not in [0, 1, 2, 3]:
            raise ValueError("岗位级别必须在 0-3 之间")
        return v


class PostResponse(BaseModel):
    """岗位响应Schema"""
    id: str
    name: str
    code: str
    post_type: int
    post_type_display: Optional[str] = None
    post_level: int
    post_level_display: Optional[str] = None
    status: bool
    description: Optional[str] = None
    dept_id: Optional[str] = None
    dept_name: Optional[str] = None
    user_count: int = 0
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PostSimple(BaseModel):
    """岗位简单输出（用于选择器）"""
    id: str
    name: str
    code: str
    post_type: int
    post_level: int
    status: bool
    
    model_config = ConfigDict(from_attributes=True)


class PostBatchDeleteIn(BaseModel):
    """批量删除岗位输入"""
    ids: List[str] = Field(..., description="要删除的岗位ID列表")


class PostBatchDeleteOut(BaseModel):
    """批量删除岗位输出"""
    count: int = Field(..., description="删除的记录数")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class PostBatchUpdateStatusIn(BaseModel):
    """批量更新岗位状态输入"""
    ids: List[str] = Field(..., description="岗位ID列表")
    status: bool = Field(..., description="岗位状态")


class PostBatchUpdateStatusOut(BaseModel):
    """批量更新岗位状态输出"""
    count: int = Field(..., description="更新的记录数")


class PostUserSchema(BaseModel):
    """岗位用户信息"""
    id: str
    name: Optional[str] = None
    username: str
    avatar: Optional[str] = None
    email: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PostUserIn(BaseModel):
    """岗位用户操作输入"""
    post_id: str = Field(..., description="岗位ID")
    user_ids: List[str] = Field(default=[], description="用户ID列表")
    user_id: Optional[str] = Field(None, description="单个用户ID")


class PostStatsResponse(BaseModel):
    """岗位统计输出"""
    total_count: int = Field(..., description="总岗位数")
    active_count: int = Field(..., description="启用岗位数")
    inactive_count: int = Field(..., description="禁用岗位数")
    type_stats: Dict[str, int] = Field(..., description="按类型统计")
    level_stats: Dict[str, int] = Field(..., description="按级别统计")


class PostSearchRequest(BaseModel):
    """搜索岗位请求"""
    keyword: str = Field(..., description="搜索关键词")
