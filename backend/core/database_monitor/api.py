#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库监控API
"""
import logging
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException

from app.config import settings
import asyncpg

from core.database_monitor.database_collector import AsyncDatabaseCollector
from core.database_monitor.schema import (
    DatabaseOverviewSchema,
    DatabaseRealtimeStatsSchema,
    DatabaseConnectionTestSchema,
    DatabaseConfigSchema
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database_monitor", tags=["数据库监控"])


async def get_all_databases_from_server(db_config: dict, db_type: str) -> List[str]:
    """从数据库服务器获取所有数据库列表（异步）"""
    databases = []

    conn = None
    try:
        if db_type == 'POSTGRESQL':
            conn = await asyncpg.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                user=db_config.get('user', ''),
                password=db_config.get('password', ''),
                database='postgres',
                timeout=5
            )
            rows = await conn.fetch("""
                SELECT datname
                FROM pg_database
                WHERE datistemplate = FALSE
                  AND datname NOT IN ('postgres')
                ORDER BY datname
            """)
            databases = [row['datname'] for row in rows]

        elif db_type == 'MYSQL':
            import aiomysql
            conn = await aiomysql.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                user=db_config.get('user', ''),
                password=db_config.get('password', ''),
                connect_timeout=5
            )
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT SCHEMA_NAME
                    FROM information_schema.SCHEMATA
                    WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                    ORDER BY SCHEMA_NAME
                """)
                rows = await cursor.fetchall()
                databases = [row[0] for row in rows]

    except Exception as e:
        logger.error(f"Failed to get databases from server: {e}")
        return []
    finally:
        if conn:
            try:
                await conn.close()
            except Exception:
                pass

    return databases


def parse_database_url(database_url: str) -> dict:
    """解析数据库URL"""
    parsed = urlparse(database_url)
    
    # 获取数据库类型
    scheme = parsed.scheme.lower()
    if 'postgresql' in scheme or 'postgres' in scheme:
        db_type = 'POSTGRESQL'
        default_port = 5432
    elif 'mysql' in scheme:
        db_type = 'MYSQL'
        default_port = 3306
    elif 'mssql' in scheme or 'sqlserver' in scheme:
        db_type = 'SQLSERVER'
        default_port = 1433
    else:
        return None
    
    # 解析连接信息
    host = parsed.hostname or 'localhost'
    port = parsed.port or default_port
    user = parsed.username or ''
    password = parsed.password or ''
    database = parsed.path.lstrip('/') if parsed.path else ''
    
    return {
        'db_type': db_type,
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database
    }


async def get_database_configs() -> List[dict]:
    """从settings中获取数据库配置（异步）"""
    configs = []
    configured_databases = []
    other_databases = []

    # 从DATABASE_URL解析配置
    database_url = settings.DATABASE_URL
    if not database_url:
        return configs

    db_info = parse_database_url(database_url)
    if not db_info:
        return configs

    db_type = db_info['db_type']
    host = db_info['host']
    port = db_info['port']
    user = db_info['user']
    password = db_info['password']
    configured_db_name = db_info['database']

    # 从服务器获取所有数据库
    all_databases = await get_all_databases_from_server({
        'host': host,
        'port': port,
        'user': user,
        'password': password
    }, db_type)

    # 如果获取失败，使用配置中的数据库
    if not all_databases:
        if configured_db_name:
            all_databases = [configured_db_name]

    # 为每个数据库创建配置
    for database_name in all_databases:
        config = {
            'name': database_name,
            'db_name': database_name,
            'db_type': db_type,
            'host': host,
            'port': port,
            'database': database_name,
            'user': user,
            'password': password,
            'has_password': bool(password),
            'is_configured': database_name == configured_db_name
        }

        if database_name == configured_db_name:
            configured_databases.append(config)
        else:
            other_databases.append(config)

    # 配置的数据库放在前面
    other_databases.sort(key=lambda x: x['name'].lower())
    configs = configured_databases + other_databases

    return configs


@router.get("/configs", response_model=List[DatabaseConfigSchema], summary="获取数据库配置列表")
async def get_database_monitor_configs():
    """获取数据库监控配置列表"""
    configs = await get_database_configs()
    return [DatabaseConfigSchema(
        name=config['name'],
        db_name=config['db_name'],
        db_type=config['db_type'],
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['user'],
        has_password=config['has_password']
    ) for config in configs]


@router.get("/{db_name}/overview", response_model=DatabaseOverviewSchema, summary="获取数据库概览信息")
async def get_database_overview(db_name: str):
    """获取数据库概览信息"""
    configs = await get_database_configs()
    db_config = next((config for config in configs if config['db_name'] == db_name), None)

    if not db_config:
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    collector = AsyncDatabaseCollector(
        db_type=db_config['db_type'],
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )

    data = await collector.get_all_info(db_name, db_config['name'])
    return DatabaseOverviewSchema(**data)


@router.get("/{db_name}/realtime", response_model=DatabaseRealtimeStatsSchema, summary="获取数据库实时统计")
async def get_database_realtime_stats(db_name: str):
    """获取数据库实时统计信息"""
    configs = await get_database_configs()
    db_config = next((config for config in configs if config['db_name'] == db_name), None)

    if not db_config:
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    collector = AsyncDatabaseCollector(
        db_type=db_config['db_type'],
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )

    data = await collector.get_realtime_stats(db_name)
    return DatabaseRealtimeStatsSchema(**data)


@router.post("/{db_name}/test", response_model=DatabaseConnectionTestSchema, summary="测试数据库连接")
async def test_database_connection(db_name: str):
    """测试数据库连接"""
    configs = await get_database_configs()
    db_config = next((config for config in configs if config['db_name'] == db_name), None)

    if not db_config:
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    collector = AsyncDatabaseCollector(
        db_type=db_config['db_type'],
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database']
    )

    result = await collector.test_connection()
    return DatabaseConnectionTestSchema(**result)
