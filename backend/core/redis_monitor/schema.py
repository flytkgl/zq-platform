#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis监控Schema
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class RedisInfoSchema(BaseModel):
    """Redis基础信息Schema"""
    redis_version: str = Field(..., description="Redis版本")
    redis_mode: str = Field(..., description="Redis模式")
    role: str = Field(..., description="角色")
    os: str = Field(..., description="操作系统")
    arch_bits: int = Field(..., description="架构位数")
    uptime_in_seconds: int = Field(..., description="运行时间(秒)")
    uptime_in_days: int = Field(..., description="运行时间(天)")
    tcp_port: int = Field(..., description="TCP端口")
    connected_clients: int = Field(..., description="连接的客户端数量")
    blocked_clients: int = Field(..., description="阻塞的客户端数量")


class RedisMemorySchema(BaseModel):
    """Redis内存信息Schema"""
    used_memory: int = Field(..., description="已使用内存(字节)")
    used_memory_human: str = Field(..., description="已使用内存(人类可读)")
    used_memory_rss: int = Field(..., description="RSS内存使用(字节)")
    used_memory_peak: int = Field(..., description="内存使用峰值(字节)")
    used_memory_peak_human: str = Field(..., description="内存使用峰值(人类可读)")
    total_system_memory: int = Field(..., description="系统总内存(字节)")
    total_system_memory_human: str = Field(..., description="系统总内存(人类可读)")
    used_memory_dataset: int = Field(..., description="数据集内存使用(字节)")
    used_memory_dataset_perc: str = Field(..., description="数据集内存使用百分比")
    allocator_allocated: int = Field(..., description="分配器已分配内存")
    allocator_active: int = Field(..., description="分配器活跃内存")
    maxmemory: int = Field(..., description="最大内存限制")
    maxmemory_human: str = Field(..., description="最大内存限制(人类可读)")
    maxmemory_policy: str = Field(..., description="内存策略")
    mem_fragmentation_ratio: float = Field(..., description="内存碎片率")


class RedisStatsSchema(BaseModel):
    """Redis统计信息Schema"""
    total_connections_received: int = Field(..., description="总连接数")
    total_commands_processed: int = Field(..., description="总命令处理数")
    instantaneous_ops_per_sec: int = Field(..., description="每秒操作数")
    total_net_input_bytes: int = Field(..., description="总输入字节数")
    total_net_output_bytes: int = Field(..., description="总输出字节数")
    instantaneous_input_kbps: float = Field(..., description="每秒输入KB")
    instantaneous_output_kbps: float = Field(..., description="每秒输出KB")
    rejected_connections: int = Field(..., description="拒绝的连接数")
    sync_full: int = Field(..., description="完整同步次数")
    sync_partial_ok: int = Field(..., description="部分同步成功次数")
    sync_partial_err: int = Field(..., description="部分同步失败次数")
    expired_keys: int = Field(..., description="过期键数量")
    evicted_keys: int = Field(..., description="被驱逐键数量")
    keyspace_hits: int = Field(..., description="键空间命中数")
    keyspace_misses: int = Field(..., description="键空间未命中数")
    pubsub_channels: int = Field(..., description="发布订阅频道数")
    pubsub_patterns: int = Field(..., description="发布订阅模式数")
    latest_fork_usec: int = Field(..., description="最近fork时间(微秒)")
    migrate_cached_sockets: int = Field(..., description="迁移缓存套接字数")


class RedisKeyspaceSchema(BaseModel):
    """Redis键空间信息Schema"""
    db_id: int = Field(..., description="数据库ID")
    keys: int = Field(..., description="键数量")
    expires: int = Field(..., description="过期键数量")
    avg_ttl: int = Field(..., description="平均TTL")


class RedisSlowLogSchema(BaseModel):
    """Redis慢日志Schema"""
    id: int = Field(..., description="日志ID")
    timestamp: int = Field(..., description="时间戳")
    duration: int = Field(..., description="执行时间(微秒)")
    command: str = Field(..., description="命令")
    client_ip: str = Field(..., description="客户端IP")
    client_name: str = Field(..., description="客户端名称")


class RedisClientSchema(BaseModel):
    """Redis客户端信息Schema"""
    id: str = Field(..., description="客户端ID")
    addr: str = Field(..., description="客户端地址")
    fd: int = Field(..., description="文件描述符")
    name: str = Field(..., description="客户端名称")
    age: int = Field(..., description="连接时长(秒)")
    idle: int = Field(..., description="空闲时间(秒)")
    flags: str = Field(..., description="客户端标志")
    db: int = Field(..., description="数据库")
    sub: int = Field(..., description="订阅频道数")
    psub: int = Field(..., description="订阅模式数")
    multi: int = Field(..., description="事务命令数")
    qbuf: int = Field(..., description="查询缓冲区长度")
    qbuf_free: int = Field(..., description="查询缓冲区剩余空间")
    obl: int = Field(..., description="输出缓冲区长度")
    oll: int = Field(..., description="输出列表长度")
    omem: int = Field(..., description="输出内存使用")
    events: str = Field(..., description="文件描述符事件")
    cmd: str = Field(..., description="最后执行的命令")


class RedisMonitorOverviewSchema(BaseModel):
    """Redis监控概览Schema"""
    connection_id: str = Field(..., description="连接ID")
    connection_name: str = Field(..., description="连接名称")
    status: str = Field(..., description="连接状态")
    info: RedisInfoSchema = Field(..., description="基础信息")
    memory: RedisMemorySchema = Field(..., description="内存信息")
    stats: RedisStatsSchema = Field(..., description="统计信息")
    keyspace: List[RedisKeyspaceSchema] = Field(default=[], description="键空间信息")
    clients: List[RedisClientSchema] = Field(default=[], description="客户端信息")
    slow_log: List[RedisSlowLogSchema] = Field(default=[], description="慢日志")
    timestamp: str = Field(..., description="时间戳")


class RedisRealtimeStatsSchema(BaseModel):
    """Redis实时统计Schema"""
    connection_id: str = Field(..., description="连接ID")
    used_memory: int = Field(..., description="已使用内存")
    memory_usage_percent: float = Field(..., description="内存使用率")
    connected_clients: int = Field(..., description="连接客户端数")
    ops_per_sec: int = Field(..., description="每秒操作数")
    hit_rate: float = Field(..., description="命中率")
    keyspace_hits: int = Field(..., description="键空间命中数")
    keyspace_misses: int = Field(..., description="键空间未命中数")
    timestamp: str = Field(..., description="时间戳")


class RedisConnectionTestSchema(BaseModel):
    """Redis连接测试Schema"""
    success: bool = Field(..., description="连接是否成功")
    message: str = Field(..., description="测试结果消息")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")
    redis_version: Optional[str] = Field(None, description="Redis版本")


class RedisConfigSchema(BaseModel):
    """Redis配置信息Schema"""
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    database: int = Field(..., description="数据库编号")
    has_password: bool = Field(..., description="是否有密码")
    redis_url: str = Field(default='', description="Redis URL")
