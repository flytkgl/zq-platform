#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单管理数据模型
"""
from sqlalchemy import Column, String, Text, Integer, Index, JSON, Boolean

from app.base_model import BaseModel


class FormMeta(BaseModel):
    """表单元数据"""
    __tablename__ = "form_meta"

    # 所属应用（逻辑外键关联 core_application）
    application_id = Column(String(21), nullable=True, index=True, comment="所属应用ID")

    name = Column(String(100), nullable=False, comment="表单名称")
    code = Column(String(100), unique=True, nullable=False, comment="表单编码")
    form_type = Column(String(20), default="normal", comment="表单类型: normal/workflow")
    description = Column(Text, default="", comment="描述")
    status = Column(String(20), default="draft", index=True, comment="状态: draft/published")
    version = Column(Integer, default=1, comment="版本号")

    # 数据源配置
    db_config = Column(String(100), nullable=False, comment="数据库配置名")
    main_table = Column(String(100), nullable=False, comment="主表名")
    main_table_schema = Column(String(100), default="", comment="主表Schema")
    main_table_database = Column(String(100), default="", comment="主表数据库")

    # 移动端配置
    show_in_mobile = Column(Boolean, default=False, comment="是否在移动端显示")

    # 图标配置
    icon = Column(String(100), default="", comment="图标")
    icon_bg_color = Column(String(200), default="", comment="图标背景色")

    # JSON 配置
    form_config = Column(JSON, default=dict, comment="表单设计配置")
    list_config = Column(JSON, default=dict, comment="列表设计配置")


class FormSubTable(BaseModel):
    """表单子表关联"""
    __tablename__ = "form_sub_table"

    # 所属表单（逻辑外键）
    form_id = Column(String(50), nullable=False, index=True, comment="所属表单ID")

    table_name = Column(String(100), nullable=False, comment="从表名")
    table_schema = Column(String(100), default="", comment="从表Schema")
    table_database = Column(String(100), default="", comment="从表数据库")
    alias = Column(String(100), default="", comment="别名")
    foreign_key = Column(String(100), nullable=False, comment="外键字段")
    related_field = Column(String(100), default="id", comment="关联主表字段")
    relation_type = Column(String(20), default="one-to-many", comment="关联类型: one-to-one/one-to-many")
