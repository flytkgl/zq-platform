#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单管理 Schema 定义
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


# ============ 表单元数据 Schema ============

class FormMetaBase(BaseModel):
    """表单基础信息"""
    application_id: Optional[str] = Field(None, description="所属应用ID")
    name: str = Field(..., description="表单名称")
    code: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", description="表单编码（字母开头，只能包含字母、数字和下划线）")
    form_type: str = Field("normal", description="表单类型: normal-普通表单, workflow-流程表单")
    description: str = Field("", description="描述")
    sort: int = Field(0, description="排序")
    show_in_mobile: bool = Field(False, description="是否在移动端显示")
    icon: str = Field("", description="图标")
    icon_bg_color: str = Field("", description="图标背景色")


class FormSubTableSchema(BaseModel):
    """子表关联配置"""
    table_name: str = Field(..., description="从表名")
    table_schema: str = Field("", description="从表Schema")
    table_database: str = Field("", description="从表数据库")
    alias: str = Field("", description="别名")
    foreign_key: str = Field(..., description="外键字段")
    related_field: str = Field("id", description="关联主表字段")
    relation_type: str = Field("one-to-many", description="关联类型")
    sort: int = Field(0, description="排序")


class FormMetaCreateIn(FormMetaBase):
    """创建表单请求"""
    db_config: str = Field(..., description="数据库配置名")
    main_table: str = Field(..., description="主表名")
    main_table_schema: str = Field("", description="主表Schema")
    main_table_database: str = Field("", description="主表数据库")
    form_config: Dict[str, Any] = Field(default_factory=dict, description="表单设计配置")
    list_config: Dict[str, Any] = Field(default_factory=dict, description="列表设计配置")
    sub_tables: List[FormSubTableSchema] = Field(default_factory=list, description="子表配置")


class FormMetaUpdateIn(BaseModel):
    """更新表单请求"""
    name: Optional[str] = Field(None, description="表单名称")
    form_type: Optional[str] = Field(None, description="表单类型")
    description: Optional[str] = Field(None, description="描述")
    sort: Optional[int] = Field(None, description="排序")
    show_in_mobile: Optional[bool] = Field(None, description="是否在移动端显示")
    icon: Optional[str] = Field(None, description="图标")
    icon_bg_color: Optional[str] = Field(None, description="图标背景色")
    db_config: Optional[str] = Field(None, description="数据库配置名")
    main_table: Optional[str] = Field(None, description="主表名")
    main_table_schema: Optional[str] = Field(None, description="主表Schema")
    main_table_database: Optional[str] = Field(None, description="主表数据库")
    form_config: Optional[Dict[str, Any]] = Field(None, description="表单设计配置")
    list_config: Optional[Dict[str, Any]] = Field(None, description="列表设计配置")
    sub_tables: Optional[List[FormSubTableSchema]] = Field(None, description="子表配置")


class FormSubTableOut(BaseModel):
    """子表关联输出"""
    id: str
    table_name: str
    table_schema: str = ""
    table_database: str = ""
    alias: str = ""
    foreign_key: str
    related_field: str = "id"
    relation_type: str = "one-to-many"
    sort: int = 0

    model_config = ConfigDict(from_attributes=True)


class FormMetaOut(BaseModel):
    """表单详情输出"""
    id: str
    name: str
    code: str
    form_type: str
    description: str = ""
    status: str
    version: int
    db_config: str
    main_table: str
    main_table_schema: str = ""
    main_table_database: str = ""
    show_in_mobile: bool = False
    icon: str = ""
    icon_bg_color: str = ""
    form_config: Dict[str, Any] = {}
    list_config: Dict[str, Any] = {}
    sort: int = 0
    sys_create_datetime: Optional[str] = None
    sys_update_datetime: Optional[str] = None
    sub_tables: List[FormSubTableOut] = []

    model_config = ConfigDict(from_attributes=True)


class FormMetaListOut(BaseModel):
    """表单列表输出"""
    id: str
    application_id: Optional[str] = None
    application_name: str = "主应用"
    application_code: str = ""
    name: str
    code: str
    form_type: str
    description: str = ""
    status: str
    version: int
    main_table: str
    show_in_mobile: bool = False
    icon: str = ""
    icon_bg_color: str = ""
    sort: int = 0
    sys_create_datetime: Optional[str] = None
    sys_update_datetime: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============ 导入导出 Schema ============

class FormExportOut(BaseModel):
    """表单配置导出"""
    name: str
    code: str
    form_type: str
    description: str = ""
    db_config: str
    main_table: str
    main_table_schema: str = ""
    main_table_database: str = ""
    form_config: Dict[str, Any] = {}
    list_config: Dict[str, Any] = {}
    sub_tables: List[FormSubTableSchema] = []


class FormImportIn(BaseModel):
    """表单配置导入"""
    name: str = Field(..., description="表单名称")
    code: str = Field(..., description="表单编码")
    form_type: str = Field("normal", description="表单类型")
    description: str = Field("", description="描述")
    db_config: str = Field(..., description="数据库配置名")
    main_table: str = Field(..., description="主表名")
    main_table_schema: str = Field("", description="主表Schema")
    main_table_database: str = Field("", description="主表数据库")
    form_config: Dict[str, Any] = Field(default_factory=dict, description="表单设计配置")
    list_config: Dict[str, Any] = Field(default_factory=dict, description="列表设计配置")
    sub_tables: List[FormSubTableSchema] = Field(default_factory=list, description="子表配置")


# ============ 发布配置 Schema ============

class FormPublishIn(BaseModel):
    """发布表单请求（含菜单配置）"""
    menu_name: str = Field(..., description="菜单名称")
    menu_parent_id: Optional[str] = Field(None, description="上级菜单ID")
    menu_icon: str = Field("lucide:file-text", description="菜单图标")
    menu_order: int = Field(0, description="菜单排序")

    # 功能开关
    allow_add: bool = Field(True, description="允许新增")
    allow_edit: bool = Field(True, description="允许编辑")
    allow_delete: bool = Field(True, description="允许删除")
    allow_export: bool = Field(True, description="允许导出")
    allow_import: bool = Field(False, description="允许导入")


# ============ 回写规则 Schema ============

WRITEBACK_EVENTS = (
    "before_create", "after_create", "before_update", "after_update",
    "before_delete", "after_delete", "before_approve", "after_approve",
    "before_unapprove", "after_unapprove",
)


class WriteBackCondition(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "not_empty"] = "eq"
    value: Any = None


class WriteBackMatchCondition(BaseModel):
    source_field: Optional[str] = Field(None, max_length=100)
    target_field: str = Field(..., min_length=1, max_length=100)
    fixed_value: Any = None


class FormWriteBackRuleBase(BaseModel):
    target_form_id: str = Field(..., min_length=1)
    name: str = Field("", max_length=255)
    is_name_auto: bool = True
    enabled: bool = True
    source_table_key: str = Field("main", min_length=1, max_length=100)
    target_table_key: str = Field("main", min_length=1, max_length=100)
    target_field: str = Field(..., min_length=1, max_length=100)
    trigger_events: List[Literal[
        "before_create", "after_create", "before_update", "after_update",
        "before_delete", "after_delete", "before_approve", "after_approve",
        "before_unapprove", "after_unapprove",
    ]] = Field(..., min_length=1)
    value_mode: Literal["custom"] = "custom"
    custom_expression: str = Field("", max_length=2000)
    writeback_operator: Literal["set", "add", "subtract"] = "set"
    execute_conditions: List[WriteBackCondition] = Field(default_factory=list)
    value_filter_conditions: List[WriteBackCondition] = Field(default_factory=list)
    match_conditions: List[WriteBackMatchCondition] = Field(default_factory=list)
    missing_target_policy: Literal["error"] = "error"
    remark: str = Field("", max_length=2000)


class FormWriteBackRuleCreateIn(FormWriteBackRuleBase):
    pass


class FormWriteBackRuleUpdateIn(FormWriteBackRuleBase):
    pass


class FormWriteBackRuleListOut(BaseModel):
    id: str
    name: str
    enabled: bool


class FormWriteBackRuleOut(FormWriteBackRuleBase):
    id: str
    source_form_id: str
    sys_create_datetime: Optional[str] = None
    sys_update_datetime: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
