#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库兼容层工具

提供跨数据库（PostgreSQL、MySQL、SQL Server）的 JSON 操作兼容函数
"""
from typing import Any, List

from sqlalchemy import func, literal, text
from sqlalchemy.sql import ColumnElement


def get_db_type() -> str:
    """
    获取当前数据库类型
    
    Returns:
        数据库类型: 'postgresql', 'mysql' 或 'sqlserver'
    """
    from app.config import settings
    
    return settings.DB_TYPE


def json_contains(column: ColumnElement, value: Any) -> ColumnElement:
    """
    JSON 数组包含检查（跨数据库兼容）
    
    检查 JSON 数组列是否包含指定值
    
    PostgreSQL: 使用 JSONB 的 @> 操作符
    MySQL: 使用 JSON_CONTAINS 函数
    SQL Server: 使用 OPENJSON + EXISTS 子查询
    
    Args:
        column: JSON 类型的列
        value: 要检查的值（会被转换为 JSON 数组）
    
    Returns:
        SQLAlchemy 条件表达式
    
    Example:
        # 检查 target_ids 是否包含 "user123"
        json_contains(Announcement.target_ids, "user123")
    """
    db_type = get_db_type()
    
    if db_type == "mysql":
        # MySQL: JSON_CONTAINS(column, JSON_ARRAY(value))
        import json
        json_value = json.dumps([value] if not isinstance(value, list) else value)
        return func.json_contains(column, json_value)
    elif db_type == "sqlserver":
        # SQL Server: 使用 LIKE 进行简单匹配（JSON 数组中包含元素）
        # 注意: 这是简化实现，适用于简单字符串值
        import json
        search_value = json.dumps(value)
        return column.like(f'%{search_value}%')
    else:
        # PostgreSQL: cast to JSONB and use contains
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        
        target_value = [value] if not isinstance(value, list) else value
        return cast(column, JSONB).contains(cast(target_value, JSONB))


def json_extract(column: ColumnElement, key: str) -> ColumnElement:
    """
    从 JSON 对象中提取值（跨数据库兼容）
    
    PostgreSQL: 使用 JSONB 的 ->> 操作符
    MySQL: 使用 JSON_EXTRACT 和 JSON_UNQUOTE 函数
    SQL Server: 使用 JSON_VALUE 函数
    
    Args:
        column: JSON 类型的列
        key: 要提取的键名
    
    Returns:
        提取的值（作为文本）
    
    Example:
        # 提取 extra_metadata 中的 "author" 字段
        json_extract(KnowledgeSegment.extra_metadata, "author")
    """
    db_type = get_db_type()
    
    if db_type == "mysql":
        # MySQL: JSON_UNQUOTE(JSON_EXTRACT(column, '$.key'))
        return func.json_unquote(func.json_extract(column, f"$.{key}"))
    elif db_type == "sqlserver":
        # SQL Server: JSON_VALUE(column, '$.key')
        return func.json_value(column, f"$.{key}")
    else:
        # PostgreSQL: cast to JSONB and use ->> operator
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        
        return cast(column, JSONB)[key].astext


def json_has_key(column: ColumnElement, key: str) -> ColumnElement:
    """
    检查 JSON 对象是否包含指定键（跨数据库兼容）
    
    PostgreSQL: 使用 JSONB 的 ? 操作符
    MySQL: 使用 JSON_CONTAINS_PATH 函数
    SQL Server: 使用 JSON_VALUE IS NOT NULL
    
    Args:
        column: JSON 类型的列
        key: 要检查的键名
    
    Returns:
        SQLAlchemy 条件表达式
    
    Example:
        # 检查 extra_metadata 是否包含 "author" 键
        json_has_key(KnowledgeSegment.extra_metadata, "author")
    """
    db_type = get_db_type()
    
    if db_type == "mysql":
        # MySQL: JSON_CONTAINS_PATH(column, 'one', '$.key')
        return func.json_contains_path(column, "one", f"$.{key}")
    elif db_type == "sqlserver":
        # SQL Server: JSON_VALUE(column, '$.key') IS NOT NULL
        return func.json_value(column, f"$.{key}").isnot(None)
    else:
        # PostgreSQL: cast to JSONB and use has_key
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        
        return cast(column, JSONB).has_key(key)


def json_array_contains_any(column: ColumnElement, values: List[Any]) -> List[ColumnElement]:
    """
    生成多个 JSON 数组包含检查条件（用于 OR 组合）
    
    Args:
        column: JSON 类型的列
        values: 要检查的值列表
    
    Returns:
        条件表达式列表，可用于 or_() 组合
    
    Example:
        # 检查 target_ids 是否包含任意一个 dept_id
        conditions = json_array_contains_any(Announcement.target_ids, dept_ids)
        query.where(or_(*conditions))
    """
    return [json_contains(column, value) for value in values]
