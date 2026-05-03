#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器监控Schema
"""
from typing import Dict, List, Any, Optional

from pydantic import BaseModel


class BasicInfoSchema(BaseModel):
    """基础系统信息"""
    hostname: str
    ip_address: str
    system: str
    platform: str
    architecture: str
    processor: str
    python_version: str
    machine: str
    node: str
    release: str
    version: str


class CpuInfoSchema(BaseModel):
    """CPU信息"""
    physical_cores: int
    total_cores: int
    cpu_percent: float
    cpu_percent_per_core: List[float]
    max_frequency: float
    min_frequency: float
    current_frequency: float
    cpu_times: Dict[str, Any]
    cpu_stats: Dict[str, Any]


class MemoryVirtualSchema(BaseModel):
    """虚拟内存信息"""
    total: float
    available: float
    used: float
    free: float
    percent: float
    active: float
    inactive: float
    buffers: float
    cached: float
    shared: float


class MemorySwapSchema(BaseModel):
    """交换内存信息"""
    total: float
    used: float
    free: float
    percent: float
    sin: float
    sout: float


class MemoryInfoSchema(BaseModel):
    """内存信息"""
    virtual: MemoryVirtualSchema
    swap: MemorySwapSchema


class DiskPartitionSchema(BaseModel):
    """磁盘分区信息"""
    device: str
    mountpoint: str
    file_system: str
    total_size: float
    used: float
    free: float
    percent: float


class DiskInfoSchema(BaseModel):
    """磁盘信息"""
    partitions: List[DiskPartitionSchema]
    total_read_bytes: float
    total_write_bytes: float
    total_read_count: int
    total_write_count: int
    total_read_time: Optional[int] = None
    total_write_time: Optional[int] = None


class NetworkTotalSchema(BaseModel):
    """网络总计信息"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    dropin: int
    dropout: int


class NetworkInterfaceStatsSchema(BaseModel):
    """网络接口统计信息"""
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    dropin: int
    dropout: int


class NetworkAddressSchema(BaseModel):
    """网络地址信息"""
    family: str
    address: str
    netmask: Optional[str] = None
    broadcast: Optional[str] = None


class NetworkInterfaceStatsDetailSchema(BaseModel):
    """网络接口详细统计"""
    is_up: bool
    duplex: str
    speed: int
    mtu: int


class NetworkInterfaceSchema(BaseModel):
    """网络接口信息"""
    addresses: List[NetworkAddressSchema]
    stats: NetworkInterfaceStatsDetailSchema


class NetworkConnectionSchema(BaseModel):
    """网络连接信息"""
    local_address: str
    status: str
    pid: Optional[int] = None


class NetworkInfoSchema(BaseModel):
    """网络信息"""
    total: NetworkTotalSchema
    per_interface: Dict[str, NetworkInterfaceStatsSchema]
    interfaces: Dict[str, NetworkInterfaceSchema]
    connections: List[NetworkConnectionSchema]


class ProcessSchema(BaseModel):
    """进程信息"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    create_time: str


class ProcessInfoSchema(BaseModel):
    """进程统计信息"""
    total_processes: int
    top_processes: List[ProcessSchema]
    running_processes: int
    sleeping_processes: int


class SystemLoadSchema(BaseModel):
    """系统负载信息"""
    load_1min: float
    load_5min: float
    load_15min: float
    cpu_count: int


class BootTimeSchema(BaseModel):
    """启动时间信息"""
    boot_time: str
    uptime_seconds: int
    uptime_formatted: str
    uptime_days: int
    uptime_hours: int
    uptime_minutes: int


class UserInfoSchema(BaseModel):
    """用户信息"""
    name: str
    terminal: Optional[str] = None
    host: Optional[str] = None
    started: Optional[str] = None
    pid: Optional[int] = None


class BatteryInfoSchema(BaseModel):
    """电池信息"""
    percent: float
    power_plugged: bool
    seconds_left: Optional[int] = None


class RealtimeStatsSchema(BaseModel):
    """实时统计信息"""
    cpu_percent: float
    memory_percent: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    network_total: Dict[str, int]
    disk_total: Dict[str, int]
    cpu_details: Dict[str, Any]
    memory_details: Dict[str, float]
    system_load: Dict[str, float]
    process_stats: Dict[str, int]
    process_info: ProcessInfoSchema
    network_interfaces: Dict[str, Dict[str, int]]
    network_connections: List[Dict[str, Any]]
    timestamp: str


class ServerMonitorResponseSchema(BaseModel):
    """服务器监控完整响应"""
    basic_info: BasicInfoSchema
    cpu_info: CpuInfoSchema
    memory_info: MemoryInfoSchema
    disk_info: DiskInfoSchema
    network_info: NetworkInfoSchema
    process_info: ProcessInfoSchema
    system_load: SystemLoadSchema
    boot_time: BootTimeSchema
    users_info: List[UserInfoSchema]
    timestamp: str
