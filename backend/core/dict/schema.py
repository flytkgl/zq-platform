#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dict Schema - 字典数据验证模式
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


class DictBase(BaseModel):
    """字典基础Schema"""
    application_id: Optional[str] = Field(None, description="所属应用ID")
    is_global: bool = Field(default=False, description="是否全局可见")
    name: str = Field(..., min_length=1, max_length=100, description="字典名称")
    code: str = Field(..., min_length=1, max_length=100, description="字典编码")
    status: bool = Field(default=True, description="状态")
    remark: Optional[str] = Field(None, description="备注")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证字典编码格式"""
        if not v:
            raise ValueError("字典编码不能为空")
        if not v.replace('_', '').isalnum():
            raise ValueError("字典编码只能包含字母、数字和下划线")
        return v


class DictCreate(DictBase):
    """字典创建Schema"""
    pass


class DictUpdate(BaseModel):
    """字典更新Schema - 所有字段可选"""
    application_id: Optional[str] = Field(None, description="所属应用ID")
    is_global: Optional[bool] = Field(None, description="是否全局可见")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="字典名称")
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="字典编码")
    status: Optional[bool] = Field(None, description="状态")
    remark: Optional[str] = Field(None, description="备注")
    sort: Optional[int] = Field(None, description="排序")
    
    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        """验证字典编码格式"""
        if v is not None:
            if not v:
                raise ValueError("字典编码不能为空")
            if not v.replace('_', '').isalnum():
                raise ValueError("字典编码只能包含字母、数字和下划线")
        return v


class DictResponse(BaseModel):
    """字典响应Schema"""
    id: str
    application_id: Optional[str] = None
    application_name: Optional[str] = None
    is_global: Optional[bool] = False
    name: str
    code: str
    status: bool
    remark: Optional[str] = None
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator("is_global", mode="before")
    @classmethod
    def coerce_is_global(cls, v):
        return bool(v) if v is not None else False


class DictSimple(BaseModel):
    """字典简单输出（用于选择器）"""
    id: str
    application_id: Optional[str] = None
    is_global: Optional[bool] = False
    name: str
    code: str
    status: bool
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator("is_global", mode="before")
    @classmethod
    def coerce_is_global(cls, v):
        return bool(v) if v is not None else False


class DictBatchDeleteIn(BaseModel):
    """批量删除字典输入"""
    ids: List[str] = Field(..., description="要删除的字典ID列表")


class DictBatchDeleteOut(BaseModel):
    """批量删除字典输出"""
    count: int = Field(..., description="删除的记录数")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class DictBatchUpdateStatusIn(BaseModel):
    """批量更新字典状态输入"""
    ids: List[str] = Field(..., description="字典ID列表")
    status: bool = Field(..., description="状态")


class DictBatchUpdateStatusOut(BaseModel):
    """批量更新字典状态输出"""
    count: int = Field(..., description="更新的记录数")


class DictSearchRequest(BaseModel):
    """搜索字典请求"""
    keyword: str = Field(..., description="搜索关键词")
