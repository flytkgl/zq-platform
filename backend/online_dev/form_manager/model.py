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


class FormWriteBackRule(BaseModel):
    """跨表单回写规则。

    规则配置使用 JSON 保存结构化条件，表达式只允许由回写表达式解析器执行，
    不保存原始 SQL 或可执行脚本。
    """

    __tablename__ = "form_writeback_rule"

    source_form_id = Column(String(21), nullable=False, index=True, comment="源表单ID")
    target_form_id = Column(String(21), nullable=False, index=True, comment="目标表单ID")
    name = Column(String(255), nullable=False, comment="规则名称")
    is_name_auto = Column(Boolean, nullable=False, default=True, comment="是否自动生成名称")
    enabled = Column(Boolean, nullable=False, default=True, index=True, comment="是否启用")

    source_table_key = Column(String(100), nullable=False, comment="源表键：main 或子表名")
    target_table_key = Column(String(100), nullable=False, comment="目标表键：main 或子表名")
    target_field = Column(String(100), nullable=False, comment="目标字段")
    trigger_events = Column(JSON, nullable=False, default=list, comment="触发事件集合")
    value_mode = Column(String(20), nullable=False, default="custom", comment="取值方式：固定为 custom")
    # 保留旧列用于兼容已存在的历史规则，新的规则不再读写此字段。
    source_value_field = Column(String(100), nullable=True, comment="历史兼容字段，已废弃")
    custom_expression = Column(Text, nullable=True, comment="安全自定义表达式")
    writeback_operator = Column(String(20), nullable=False, default="set", comment="set/add/subtract")

    execute_conditions = Column(JSON, nullable=True, comment="执行条件")
    value_filter_conditions = Column(JSON, nullable=True, comment="汇总过滤条件")
    match_conditions = Column(JSON, nullable=False, default=list, comment="源目标关联条件")
    missing_target_policy = Column(String(20), nullable=False, default="error", comment="目标不存在处理方式")
    remark = Column(Text, nullable=True, default="", comment="备注")

    __table_args__ = (
        Index("idx_form_writeback_source_enabled", "source_form_id", "enabled"),
    )
