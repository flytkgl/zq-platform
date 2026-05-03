#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单数据操作 Schema 定义
"""
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class FormDataCreateIn(BaseModel):
    """表单数据新增请求"""
    main: Dict[str, Any] = Field(..., description="主表数据")
    sub_tables: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="子表数据")


class FormDataUpdateIn(BaseModel):
    """表单数据更新请求"""
    main: Dict[str, Any] = Field(..., description="主表数据")
    sub_tables: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="子表数据")


class FormDataListOut(BaseModel):
    """表单数据列表输出"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class FormDataImportResult(BaseModel):
    """导入结果"""
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误详情")
