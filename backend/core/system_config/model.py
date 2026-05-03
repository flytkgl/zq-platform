#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SystemConfig Model - 系统配置模型
用于存储 SSO 登录和消息通知等可在前端管理的系统配置
"""
from sqlalchemy import Column, String, Text, Boolean

from app.base_model import BaseModel


class SystemConfig(BaseModel):
    """
    系统配置表

    字段说明：
    - config_group: 配置分组（如 oauth_gitee, notify_email）
    - config_key: 配置键（同一分组内唯一）
    - config_value: 配置值（明文或加密存储）
    - description: 配置描述
    - is_secret: 是否为敏感字段（API 返回时脱敏）
    - status: 是否启用
    """
    __tablename__ = "core_system_config"

    config_group = Column(String(50), nullable=False, index=True, comment="配置分组")
    config_key = Column(String(100), nullable=False, index=True, comment="配置键")
    config_value = Column(Text, nullable=True, comment="配置值")
    description = Column(String(200), nullable=True, comment="配置描述")
    is_secret = Column(Boolean, default=False, comment="是否敏感字段")
    status = Column(Boolean, default=True, index=True, comment="是否启用")

    def __str__(self):
        return f"{self.config_group}.{self.config_key}"
