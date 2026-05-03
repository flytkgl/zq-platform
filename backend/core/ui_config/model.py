#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI Config Model - UI配置模型
用于存储前端UI偏好配置
"""
from sqlalchemy import Column, String, Text, Boolean

from app.base_model import BaseModel


class UIConfig(BaseModel):
    """
    UI配置表
    
    字段说明：
    - application_id: 所属应用ID（空为主应用配置）
    - config_key: 配置键（同一应用内唯一）
    - config_value: 配置值（JSON格式）
    - config_type: 配置类型（preferences/theme/logo等）
    - description: 配置描述
    - status: 状态
    """
    __tablename__ = "core_ui_config"
    
    # 所属应用（逻辑外键关联 core_application，空为主应用配置）
    application_id = Column(String(21), nullable=True, index=True, comment="所属应用ID")
    
    # 配置键（同一应用内唯一，通过代码逻辑保证）
    config_key = Column(String(100), nullable=False, index=True, comment="配置键")
    
    # 配置值（JSON格式）
    config_value = Column(Text, nullable=True, comment="配置值(JSON)")
    
    # 配置类型
    config_type = Column(String(50), nullable=False, default="preferences", index=True, comment="配置类型")
    
    # 配置描述
    description = Column(String(200), nullable=True, comment="配置描述")
    
    # 状态
    status = Column(Boolean, default=True, index=True, comment="状态")
    
    def __str__(self):
        return f"{self.config_key} ({self.config_type})"
