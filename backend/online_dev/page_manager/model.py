#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
页面管理数据模型
"""
from sqlalchemy import Column, String, Text, Integer, JSON

from app.base_model import BaseModel


class PageMeta(BaseModel):
    """页面元数据"""
    __tablename__ = "page_meta"

    # 所属应用（逻辑外键关联 core_application）
    application_id = Column(String(21), nullable=True, index=True, comment="所属应用ID")

    name = Column(String(100), nullable=False, comment="页面名称")
    code = Column(String(100), unique=True, nullable=False, comment="页面编码")
    category = Column(String(50), default="", comment="分类")
    description = Column(Text, default="", comment="描述")
    status = Column(String(20), default="draft", index=True, comment="状态: draft/published")
    version = Column(Integer, default=1, comment="版本号")

    # 页面配置（存储 dashboard-design 的配置）
    page_config = Column(JSON, default=dict, comment="页面设计配置")
