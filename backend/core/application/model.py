#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用管理数据模型
"""
from sqlalchemy import Column, String, Text, Integer, JSON

from app.base_model import BaseModel


class Application(BaseModel):
    """应用模型 - 低代码平台的顶层容器"""
    __tablename__ = "core_application"

    name = Column(String(100), nullable=False, comment="应用名称")
    code = Column(String(100), unique=True, nullable=False, index=True, comment="应用编码（唯一标识，用于URL路由）")
    description = Column(Text, default="", comment="应用描述")
    icon = Column(String(100), default="", comment="应用图标")
    cover = Column(String(500), default="", comment="应用封面图URL")
    
    # 应用类型：form-表单应用, workflow-流程应用, dashboard-数据应用, screen-大屏应用, mixed-混合应用, ai-AI应用
    app_type = Column(String(20), default="mixed", index=True, comment="应用类型")
    
    # 状态：draft-开发中, published-已发布, disabled-已停用
    status = Column(String(20), default="draft", index=True, comment="应用状态")
    
    # 应用首页路径
    home_path = Column(String(200), nullable=True, comment="应用首页路径")
    
    # 版本号
    version = Column(Integer, default=1, comment="版本号")
    
    # 应用配置（JSON格式，可存储主题、权限、自定义配置等）
    config = Column(JSON, default=dict, comment="应用配置")
    
    # 所有者（逻辑外键关联 core_user）
    owner_id = Column(String(21), nullable=True, index=True, comment="所有者ID")
    
    # 团队成员ID列表（JSON数组）
    team_ids = Column(JSON, default=list, comment="团队成员ID列表")
    
    # 开发模式下显示的系统菜单ID列表（JSON数组）
    # 如果为空或None，则显示所有系统菜单；否则只显示选中的系统菜单
    system_menu_ids = Column(JSON, default=list, comment="开发模式下显示的系统菜单ID列表")
