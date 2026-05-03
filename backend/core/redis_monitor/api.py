#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis监控API
"""
from fastapi import APIRouter

from app.config import settings
from core.redis_monitor.redis_collector import AsyncRedisInfoCollector
from core.redis_monitor.schema import (
    RedisMonitorOverviewSchema,
    RedisRealtimeStatsSchema,
    RedisConnectionTestSchema,
    RedisConfigSchema,
)

router = APIRouter(prefix="/redis_monitor", tags=["Redis监控"])


def get_redis_config():
    """获取项目Redis配置"""
    redis_host = settings.REDIS_HOST
    redis_port = settings.REDIS_PORT
    redis_password = settings.REDIS_PASSWORD
    redis_db = settings.REDIS_DB

    # 如果密码为空字符串，设置为None
    if redis_password == '':
        redis_password = None

    return redis_host, redis_port, redis_password, redis_db


@router.get("/overview", response_model=RedisMonitorOverviewSchema, summary="获取Redis监控概览")
async def get_redis_monitor_overview():
    """获取Redis监控概览信息"""
    redis_host, redis_port, redis_password, redis_db = get_redis_config()

    collector = AsyncRedisInfoCollector(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=redis_db
    )

    data = await collector.get_all_info('project_redis', '项目Redis')
    return RedisMonitorOverviewSchema(**data)


@router.get("/realtime", response_model=RedisRealtimeStatsSchema, summary="获取Redis实时统计")
async def get_redis_realtime_stats():
    """获取Redis实时统计信息"""
    redis_host, redis_port, redis_password, redis_db = get_redis_config()

    collector = AsyncRedisInfoCollector(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=redis_db
    )

    data = await collector.get_realtime_stats('project_redis')
    return RedisRealtimeStatsSchema(**data)


@router.post("/test", response_model=RedisConnectionTestSchema, summary="测试Redis连接")
async def test_redis_connection():
    """测试Redis连接"""
    redis_host, redis_port, redis_password, redis_db = get_redis_config()

    collector = AsyncRedisInfoCollector(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=redis_db
    )

    result = await collector.test_connection()
    return RedisConnectionTestSchema(**result)


@router.get("/config", response_model=RedisConfigSchema, summary="获取Redis配置")
def get_redis_config_info():
    """获取Redis配置信息"""
    redis_host, redis_port, redis_password, redis_db = get_redis_config()

    return RedisConfigSchema(
        host=redis_host,
        port=redis_port,
        database=redis_db,
        has_password=bool(redis_password),
        redis_url=settings.REDIS_URL or ''
    )
