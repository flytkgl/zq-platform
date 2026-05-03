#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DictItem Schema - 字典项数据验证模式
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.base_schema import CSTDatetime


class DictItemBase(BaseModel):
    """字典项基础Schema"""
    dict_id: str = Field(..., description="字典ID")
    label: Optional[str] = Field(None, max_length=100, description="显示名称")
    value: Optional[str] = Field(None, max_length=100, description="实际值")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    status: bool = Field(default=True, description="状态")
    remark: Optional[str] = Field(None, description="备注")
    sort: int = Field(default=0, description="排序")


class DictItemCreate(DictItemBase):
    """字典项创建Schema"""
    pass


class DictItemUpdate(BaseModel):
    """字典项更新Schema - 所有字段可选"""
    dict_id: Optional[str] = Field(None, description="字典ID")
    label: Optional[str] = Field(None, max_length=100, description="显示名称")
    value: Optional[str] = Field(None, max_length=100, description="实际值")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    status: Optional[bool] = Field(None, description="状态")
    remark: Optional[str] = Field(None, description="备注")
    sort: Optional[int] = Field(None, description="排序")


class DictItemResponse(BaseModel):
    """字典项响应Schema"""
    id: str
    dict_id: str
    dict_code: Optional[str] = None
    dict_name: Optional[str] = None
    label: Optional[str] = None
    value: Optional[str] = None
    icon: Optional[str] = None
    status: bool
    remark: Optional[str] = None
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DictItemSimple(BaseModel):
    """字典项简单输出（用于选择器）"""
    id: str
    label: Optional[str] = None
    value: Optional[str] = None
    icon: Optional[str] = None
    status: bool
    
    model_config = ConfigDict(from_attributes=True)


class DictItemBatchDeleteIn(BaseModel):
    """批量删除字典项输入"""
    ids: List[str] = Field(..., description="要删除的字典项ID列表")


class DictItemBatchDeleteOut(BaseModel):
    """批量删除字典项输出"""
    count: int = Field(..., description="删除的记录数")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class DictItemBatchUpdateStatusIn(BaseModel):
    """批量更新字典项状态输入"""
    ids: List[str] = Field(..., description="字典项ID列表")
    status: bool = Field(..., description="状态")


class DictItemBatchUpdateStatusOut(BaseModel):
    """批量更新字典项状态输出"""
    count: int = Field(..., description="更新的记录数")


class DictItemSearchRequest(BaseModel):
    """搜索字典项请求"""
    keyword: str = Field(..., description="搜索关键词")
