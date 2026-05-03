#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Source Schema - 数据源数据验证模式
"""
from datetime import datetime
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from app.base_schema import CSTDatetime


class DataSourceBase(BaseModel):
    """数据源基础Schema"""
    application_id: Optional[str] = Field(None, description="所属应用ID")
    name: str = Field(..., description="数据源名称")
    code: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", description="数据源编码（字母开头，只能包含字母、数字和下划线）")
    source_type: str = Field(default='static', description="数据源类型: api/sql/static")
    description: str = Field(default='', description="描述说明")
    status: bool = Field(default=True, description="是否启用")
    
    # API 配置
    api_url: str = Field(default='', description="API地址")
    api_method: str = Field(default='GET', description="请求方法: GET/POST/PUT/DELETE/PATCH")
    api_headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    api_query_params: List[Dict[str, Any]] = Field(default_factory=list, description="Query参数列表")
    api_body_type: str = Field(default='none', description="请求体类型: none/json/form-data/x-www-form-urlencoded/raw")
    api_body: Dict[str, Any] = Field(default_factory=dict, description="请求体模板")
    api_content_type: str = Field(default='', description="Content-Type，raw模式时使用")
    api_timeout: int = Field(default=30, description="超时时间")
    api_data_path: str = Field(default='', description="响应数据路径")
    
    # API 认证配置
    api_auth_type: str = Field(default='none', description="认证类型: none/bearer_token/basic_auth/api_key")
    api_auth_config: Dict[str, Any] = Field(default_factory=dict, description="认证配置")
    
    # API 高级配置
    api_retry_count: int = Field(default=0, description="重试次数")
    api_retry_interval: int = Field(default=1, description="重试间隔（秒）")
    api_success_condition: Dict[str, Any] = Field(default_factory=dict, description="成功条件")
    api_proxy: str = Field(default='', description="代理地址")
    api_follow_redirects: bool = Field(default=True, description="是否跟随重定向")
    api_verify_ssl: bool = Field(default=True, description="是否验证SSL证书")
    
    # SQL 配置
    sql_content: str = Field(default='', description="SQL语句")
    db_connection: str = Field(default='default', description="数据库连接")
    
    # 静态数据
    static_data: List[Any] = Field(default_factory=list, description="静态数据")
    
    # 参数定义
    params: List[Dict[str, Any]] = Field(default_factory=list, description="参数定义")
    
    # 结果处理
    result_type: str = Field(default='list', description="结果类型")
    tree_config: Dict[str, Any] = Field(default_factory=dict, description="树形配置")
    field_mapping: Dict[str, str] = Field(default_factory=dict, description="字段映射")
    chart_config: Dict[str, Any] = Field(default_factory=dict, description="图表配置")
    
    # 缓存配置
    cache_enabled: bool = Field(default=False, description="是否启用缓存")
    cache_ttl: int = Field(default=300, description="缓存时间")


class DataSourceCreate(DataSourceBase):
    """数据源创建Schema"""
    pass


class DataSourceUpdate(BaseModel):
    """数据源更新Schema"""
    application_id: Optional[str] = None
    name: Optional[str] = None
    code: Optional[str] = Field(None, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", description="数据源编码（字母开头，只能包含字母、数字和下划线）")
    source_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[bool] = None
    
    api_url: Optional[str] = None
    api_method: Optional[str] = None
    api_headers: Optional[Dict[str, str]] = None
    api_query_params: Optional[List[Dict[str, Any]]] = None
    api_body_type: Optional[str] = None
    api_body: Optional[Dict[str, Any]] = None
    api_content_type: Optional[str] = None
    api_timeout: Optional[int] = None
    api_data_path: Optional[str] = None
    api_auth_type: Optional[str] = None
    api_auth_config: Optional[Dict[str, Any]] = None
    api_retry_count: Optional[int] = None
    api_retry_interval: Optional[int] = None
    api_success_condition: Optional[Dict[str, Any]] = None
    api_proxy: Optional[str] = None
    api_follow_redirects: Optional[bool] = None
    api_verify_ssl: Optional[bool] = None
    
    sql_content: Optional[str] = None
    db_connection: Optional[str] = None
    
    static_data: Optional[List[Any]] = None
    params: Optional[List[Dict[str, Any]]] = None
    
    result_type: Optional[str] = None
    tree_config: Optional[Dict[str, Any]] = None
    field_mapping: Optional[Dict[str, str]] = None
    chart_config: Optional[Dict[str, Any]] = None
    
    cache_enabled: Optional[bool] = None
    cache_ttl: Optional[int] = None


class DataSourceResponse(DataSourceBase):
    """数据源响应Schema"""
    id: str
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)


class DataSourceSimpleOut(BaseModel):
    """数据源简单输出（用于下拉选择）"""
    id: str
    application_id: Optional[str] = None
    name: str
    code: str
    source_type: str
    result_type: str = "list"
    description: str = ""

    model_config = ConfigDict(from_attributes=True)


class DataSourcePreviewRequest(BaseModel):
    """数据源预览请求"""
    params: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=100, ge=1, le=1000)


class DataSourceExecuteRequest(BaseModel):
    """数据源执行请求"""
    params: Dict[str, Any] = Field(default_factory=dict)


class DataSourceTestRequest(BaseModel):
    """数据源测试请求（临时配置）"""
    source_type: str
    # API 配置
    api_url: str = ""
    api_method: str = "GET"
    api_headers: Dict[str, str] = Field(default_factory=dict)
    api_query_params: List[Dict[str, Any]] = Field(default_factory=list)
    api_body_type: str = "none"
    api_body: Dict[str, Any] = Field(default_factory=dict)
    api_content_type: str = ""
    api_timeout: int = 30
    api_data_path: str = ""
    # API 认证
    api_auth_type: str = "none"
    api_auth_config: Dict[str, Any] = Field(default_factory=dict)
    # API 高级
    api_retry_count: int = 0
    api_retry_interval: int = 1
    api_success_condition: Dict[str, Any] = Field(default_factory=dict)
    api_proxy: str = ""
    api_follow_redirects: bool = True
    api_verify_ssl: bool = True
    # SQL 配置
    sql_content: str = ""
    db_connection: str = "default"
    # 静态数据
    static_data: List[Any] = Field(default_factory=list)
    # 参数
    params_def: List[Dict[str, Any]] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)
    # 结果处理
    result_type: str = "list"
    tree_config: Dict[str, Any] = Field(default_factory=dict)
    field_mapping: Dict[str, str] = Field(default_factory=dict)
    chart_config: Dict[str, Any] = Field(default_factory=dict)


class DataSourceCopyRequest(BaseModel):
    """数据源复制请求"""
    new_code: str = Field(..., description="新编码")
    new_name: str = Field(default="", description="新名称")


class TableRelation(BaseModel):
    """表关系定义"""
    id: str = Field(default="", description="关系ID")
    sourceTable: str = Field(..., description="源表名")
    sourceField: str = Field(..., description="源字段名")
    targetTable: str = Field(..., description="目标表名")
    targetField: str = Field(..., description="目标字段名")
    relationType: str = Field(default="many-to-one", description="关系类型")


class AIGenerateSqlRequest(BaseModel):
    """AI 生成 SQL 请求"""
    model_config = ConfigDict(protected_namespaces=())
    
    user_question: str = Field(..., description="用户问题（自然语言描述）")
    db_connection: str = Field(default="default", description="数据库连接名称")
    database: str = Field(default="", description="数据库名")
    schema_name: str = Field(default="", description="Schema 名称")
    selected_tables: List[str] = Field(default_factory=list, description="选中的表名列表")
    table_fields: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="表字段信息")
    table_relations: List[TableRelation] = Field(default_factory=list, description="表关系列表")
    include_table_relations: bool = Field(default=True, description="是否包含表关系信息")
    model_id: str = Field(..., description="LLM 模型 ID")


class AIGenerateSqlResponse(BaseModel):
    """AI 生成 SQL 响应"""
    sql: str = Field(..., description="生成的 SQL 语句")
    thought: str = Field(default="", description="生成思路")
    params: List[Dict[str, Any]] = Field(default_factory=list, description="推荐的参数定义")
