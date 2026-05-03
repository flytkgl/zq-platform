#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
签名令牌模型
用于手机扫码签名功能
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.base_model import BaseModel


class SignatureToken(BaseModel):
    """签名令牌"""
    __tablename__ = "core_signature_token"

    token = Column(String(128), unique=True, nullable=False, index=True, comment="令牌")
    source = Column(String(50), nullable=True, comment="来源(form/workflow等)")
    callback_key = Column(String(128), nullable=True, comment="回调标识(用于前端轮询)")
    expired_at = Column(DateTime, nullable=False, comment="过期时间")
    is_used = Column(Boolean, default=False, comment="是否已使用")
    used_at = Column(DateTime, nullable=True, comment="使用时间")
    signature_file_id = Column(String(36), nullable=True, comment="签名文件ID")
    user_id = Column(String(36), nullable=True, comment="创建用户ID")
    ip_address = Column(String(64), nullable=True, comment="签名IP地址")
    user_agent = Column(Text, nullable=True, comment="签名设备信息")
