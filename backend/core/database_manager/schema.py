#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库管理Schema
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============ 数据库相关 ============
class DatabaseInfo(BaseModel):
    """数据库信息"""
    name: str
    owner: Optional[str] = None
    encoding: Optional[str] = None
    collation: Optional[str] = None
    size: Optional[str] = None
    size_bytes: Optional[int] = None
    tables_count: Optional[int] = None
    description: Optional[str] = None


class DatabaseCreateIn(BaseModel):
    """创建数据库输入"""
    name: str
    owner: Optional[str] = None
    encoding: Optional[str] = "UTF8"
    charset: Optional[str] = "utf8mb4"  # MySQL
    collation: Optional[str] = None
    template: Optional[str] = "template0"  # PostgreSQL


class DatabaseOperationOut(BaseModel):
    """数据库操作输出"""
    success: bool
    message: str


# ============ Schema相关（PostgreSQL） ============
class SchemaInfo(BaseModel):
    """Schema信息"""
    name: str
    owner: Optional[str] = None
    tables_count: Optional[int] = None


# ============ 表相关 ============
class TableInfo(BaseModel):
    """表信息"""
    schema_name: Optional[str] = None
    table_name: str
    table_type: Optional[str] = "BASE TABLE"
    row_count: Optional[int] = None
    total_size: Optional[str] = None
    total_size_bytes: Optional[int] = None
    table_size: Optional[str] = None
    table_size_bytes: Optional[int] = None
    indexes_size: Optional[str] = None
    indexes_size_bytes: Optional[int] = None
    data_length: Optional[int] = None  # MySQL
    index_length: Optional[int] = None  # MySQL
    description: Optional[str] = None


# ============ 视图相关 ============
class ViewInfo(BaseModel):
    """视图信息"""
    schema_name: Optional[str] = None
    view_name: str
    view_definition: Optional[str] = None
    is_updatable: Optional[bool] = None
    check_option: Optional[str] = None
    view_type: Optional[str] = "VIEW"
    description: Optional[str] = None


class ViewColumn(BaseModel):
    """视图列信息"""
    column_name: str
    data_type: str
    is_nullable: Optional[bool] = None
    ordinal_position: Optional[int] = None
    description: Optional[str] = None


class ViewStructure(BaseModel):
    """视图结构详情"""
    view_info: ViewInfo
    columns: List[ViewColumn]
    dependencies: List[str]
    definition_sql: str


# ============ 列信息 ============
class ColumnInfo(BaseModel):
    """字段信息"""
    column_name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    ordinal_position: Optional[int] = None
    is_primary_key: bool = False
    is_unique: bool = False
    description: Optional[str] = None


class IndexInfo(BaseModel):
    """索引信息"""
    index_name: str
    index_type: Optional[str] = None
    columns: str
    is_unique: bool = False
    is_primary: bool = False
    definition: Optional[str] = None


class ConstraintInfo(BaseModel):
    """约束信息"""
    constraint_name: str
    constraint_type: str
    columns: Optional[str] = None
    definition: Optional[str] = None
    referenced_table: Optional[str] = None
    referenced_columns: Optional[str] = None


class TableStructure(BaseModel):
    """表结构详情"""
    table_info: TableInfo
    columns: List[ColumnInfo]
    indexes: List[IndexInfo]
    constraints: List[ConstraintInfo]


# ============ 数据查询相关 ============
class QueryDataIn(BaseModel):
    """查询数据输入"""
    table_name: str
    schema_name: Optional[str] = None
    page: int = 1
    page_size: int = 20
    where: Optional[str] = None
    order_by: Optional[str] = None


class QueryDataOut(BaseModel):
    """查询数据输出"""
    columns: List[str]
    rows: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


# ============ SQL执行相关 ============
class ExecuteSQLIn(BaseModel):
    """执行SQL输入"""
    sql: str
    is_query: bool = True


class ExecuteSQLOut(BaseModel):
    """执行SQL输出"""
    success: bool
    message: str
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    affected_rows: Optional[int] = None
    execution_time: float


# ============ 数据操作相关 ============
class InsertDataIn(BaseModel):
    """插入数据"""
    table_name: str
    schema_name: Optional[str] = None
    data: Dict[str, Any]


class UpdateDataIn(BaseModel):
    """更新数据"""
    table_name: str
    schema_name: Optional[str] = None
    data: Dict[str, Any]
    where: str


class DeleteDataIn(BaseModel):
    """删除数据"""
    table_name: str
    schema_name: Optional[str] = None
    where: str


class DataOperationOut(BaseModel):
    """数据操作输出"""
    success: bool
    message: str
    affected_rows: int


# ============ DDL操作相关 ============
class ExecuteDDLIn(BaseModel):
    """执行DDL输入"""
    sql: str = Field(..., description="DDL SQL语句")
    database: Optional[str] = Field(None, description="数据库名")
    schema_name: Optional[str] = Field(None, description="Schema名")


class ExecuteDDLOut(BaseModel):
    """执行DDL输出"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="执行消息")
    affected_rows: int = Field(default=0, description="影响行数")


# ============ 数据库配置相关 ============
class DatabaseConfig(BaseModel):
    """数据库配置信息"""
    db_name: str
    name: str
    db_type: str
    host: str
    port: int
    database: str
    user: str
    has_password: bool
