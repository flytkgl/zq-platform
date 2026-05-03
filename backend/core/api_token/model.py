#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Token 数据模型
个人访问令牌，用于API调用认证
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text

from app.base_model import BaseModel


class ApiToken(BaseModel):
    """API Token 模型"""
    __tablename__ = "core_api_token"

    name = Column(String(100), nullable=False, comment="令牌名称")
    token_hash = Column(String(64), nullable=False, unique=True, index=True, comment="令牌哈希值(SHA-256)")
    token_prefix = Column(String(255), nullable=False, comment="令牌前缀(用于识别)")
    user_id = Column(String(21), nullable=False, index=True, comment="所属用户ID")
    expires_at = Column(DateTime, nullable=True, comment="过期时间(NULL表示永不过期)")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")
    description = Column(Text, nullable=True, comment="令牌描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
