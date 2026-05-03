#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Token Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.base_schema import CSTDatetime


class ApiTokenCreate(BaseModel):
    """创建API Token请求"""
    name: str = Field(..., min_length=1, max_length=100, description="令牌名称")
    expires_at: Optional[datetime] = Field(None, description="过期时间(不传表示永不过期)")
    description: Optional[str] = Field(None, max_length=500, description="令牌描述")


class ApiTokenResponse(BaseModel):
    """API Token响应（列表展示用，不包含完整token）"""
    id: str
    name: str
    token_prefix: str = Field(description="令牌前缀，用于识别")
    expires_at: Optional[CSTDatetime] = None
    last_used_at: Optional[CSTDatetime] = None
    description: Optional[str] = None
    is_active: bool
    sys_create_datetime: Optional[CSTDatetime] = None

    class Config:
        from_attributes = True


class ApiTokenCreateResponse(BaseModel):
    """创建API Token的响应（仅创建时返回一次完整token）"""
    id: str
    name: str
    token: str = Field(description="完整的API Token（仅此一次展示，请妥善保存）")
    token_prefix: str
    expires_at: Optional[CSTDatetime] = None
    description: Optional[str] = None
    sys_create_datetime: Optional[CSTDatetime] = None
