#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
临时访问令牌模型
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index

from app.base_model import BaseModel


class FileAccessToken(BaseModel):
    """文件临时访问令牌模型"""
    __tablename__ = "core_file_access_token"

    token = Column(String(64), unique=True, nullable=False, comment="临时访问令牌")
    file_id = Column(String(36), nullable=False, comment="文件ID")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    user_id = Column(String(36), nullable=True, comment="用户ID")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User Agent")

    __table_args__ = (
        Index('ix_file_access_token_token', 'token'),
        Index('ix_file_access_token_file_id', 'file_id'),
        Index('ix_file_access_token_expires_at', 'expires_at'),
    )
