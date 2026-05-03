#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库监控Schema
"""
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class DatabaseBasicInfoSchema(BaseModel):
    """数据库基本信息Schema"""
    db_type: str
    host: str
    port: int
    database: str
    version: str
    uptime: str
    timezone: str
    charset: str


class DatabaseConnectionInfoSchema(BaseModel):
    """数据库连接信息Schema"""
    total_connections: int
    max_connections: int
    active_connections: int
    idle_connections: int
    connection_usage_percent: float


class DatabaseSizeSchema(BaseModel):
    """数据库大小信息Schema"""
    database_size_bytes: int
    database_size_mb: float
    database_size_gb: float


class DatabasePerformanceStatsSchema(BaseModel):
    """数据库性能统计Schema"""
    # PostgreSQL
    total_backends: Optional[int] = None
    transactions_commit: Optional[int] = None
    transactions_rollback: Optional[int] = None
    tuples_returned: Optional[int] = None
    tuples_fetched: Optional[int] = None
    tuples_inserted: Optional[int] = None
    tuples_updated: Optional[int] = None
    tuples_deleted: Optional[int] = None

    # MySQL
    total_queries: Optional[int] = None
    total_connections: Optional[int] = None
    slow_queries: Optional[int] = None
    bytes_received: Optional[int] = None
    bytes_sent: Optional[int] = None

    # SQL Server
    batch_requests_per_sec: Optional[int] = None
    page_life_expectancy: Optional[int] = None
    buffer_cache_hit_ratio: Optional[float] = None

    # 通用
    cache_hit_ratio: float = 0.0


class DatabaseTableStatsSchema(BaseModel):
    """数据库表统计Schema"""
    # PostgreSQL
    schemaname: Optional[str] = None
    tablename: Optional[str] = None
    inserts: Optional[int] = None
    updates: Optional[int] = None
    deletes: Optional[int] = None
    live_tuples: Optional[int] = None
    dead_tuples: Optional[int] = None
    size: Optional[str] = None

    # MySQL
    table_name: Optional[str] = None
    table_rows: Optional[int] = None
    data_length: Optional[int] = None
    index_length: Optional[int] = None
    total_size: Optional[int] = None
    auto_increment: Optional[int] = None

    # SQL Server
    total_size_kb: Optional[int] = None
    used_size_kb: Optional[int] = None
    data_size_kb: Optional[int] = None


class DatabaseOverviewSchema(BaseModel):
    """数据库概览Schema"""
    connection_id: str
    connection_name: str
    status: str
    basic_info: Dict[str, Any]
    connection_info: Dict[str, Any]
    database_size: Dict[str, Any]
    performance_stats: Dict[str, Any]
    table_stats: List[Dict[str, Any]]
    timestamp: str


class DatabaseRealtimeStatsSchema(BaseModel):
    """数据库实时统计Schema"""
    connection_id: str
    connections_used: int
    connection_usage_percent: float
    database_size_mb: float
    cache_hit_ratio: float
    active_connections: int
    timestamp: str


class DatabaseConnectionTestSchema(BaseModel):
    """数据库连接测试Schema"""
    success: bool
    message: str
    response_time: Optional[float] = None
    version: Optional[str] = None
    db_type: str


class DatabaseConfigSchema(BaseModel):
    """数据库配置Schema"""
    name: str
    db_name: str
    db_type: str
    host: str
    port: int
    database: str
    user: str
    has_password: bool
