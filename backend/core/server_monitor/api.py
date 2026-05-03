#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器监控API（异步版本）
"""
import asyncio
from typing import Dict, Any, List, Optional

from fastapi import APIRouter

from core.server_monitor.server_info import ServerInfoCollector
from core.server_monitor.schema import (
    ServerMonitorResponseSchema,
    RealtimeStatsSchema,
    BatteryInfoSchema,
    BasicInfoSchema,
    CpuInfoSchema,
    MemoryInfoSchema,
    DiskInfoSchema,
    NetworkInfoSchema,
    ProcessInfoSchema,
    SystemLoadSchema,
    BootTimeSchema,
    UserInfoSchema,
)

router = APIRouter(prefix="/server_monitor", tags=["服务器监控"])

# 创建全局的服务器信息收集器实例
server_collector = ServerInfoCollector()


def _get_default_overview_error(error_msg: str) -> Dict[str, Any]:
    """获取默认的错误响应"""
    return {
        "basic_info": {
            "hostname": "error",
            "ip_address": "error",
            "system": "error",
            "platform": error_msg,
            "architecture": "error",
            "processor": "error",
            "python_version": "error",
            "machine": "error",
            "node": "error",
            "release": "error",
            "version": "error"
        },
        "cpu_info": {
            "physical_cores": 0,
            "total_cores": 0,
            "cpu_percent": 0.0,
            "cpu_percent_per_core": [],
            "max_frequency": 0.0,
            "min_frequency": 0.0,
            "current_frequency": 0.0,
            "cpu_times": {},
            "cpu_stats": {}
        },
        "memory_info": {
            "virtual": {
                "total": 0.0,
                "available": 0.0,
                "used": 0.0,
                "free": 0.0,
                "percent": 0.0,
                "active": 0.0,
                "inactive": 0.0,
                "buffers": 0.0,
                "cached": 0.0,
                "shared": 0.0
            },
            "swap": {
                "total": 0.0,
                "used": 0.0,
                "free": 0.0,
                "percent": 0.0,
                "sin": 0.0,
                "sout": 0.0
            }
        },
        "disk_info": {
            "partitions": [],
            "total_read_bytes": 0.0,
            "total_write_bytes": 0.0,
            "total_read_count": 0,
            "total_write_count": 0
        },
        "network_info": {
            "total": {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0,
                "errin": 0,
                "errout": 0,
                "dropin": 0,
                "dropout": 0
            },
            "per_interface": {},
            "interfaces": {},
            "connections": []
        },
        "process_info": {
            "total_processes": 0,
            "top_processes": [],
            "running_processes": 0,
            "sleeping_processes": 0
        },
        "system_load": {
            "load_1min": 0.0,
            "load_5min": 0.0,
            "load_15min": 0.0,
            "cpu_count": 0
        },
        "boot_time": {
            "boot_time": "",
            "uptime_seconds": 0,
            "uptime_formatted": "",
            "uptime_days": 0,
            "uptime_hours": 0,
            "uptime_minutes": 0
        },
        "users_info": [],
        "timestamp": ""
    }


@router.get("/overview", response_model=ServerMonitorResponseSchema, summary="获取服务器完整监控信息")
async def get_server_overview():
    """获取服务器完整监控信息"""
    try:
        data = await asyncio.to_thread(server_collector.get_all_info)
        return data
    except Exception as e:
        print(f"Error in get_server_overview: {e}")
        return _get_default_overview_error(str(e))


@router.get("/realtime", response_model=RealtimeStatsSchema, summary="获取实时统计信息")
async def get_realtime_stats():
    """获取实时统计信息"""
    try:
        return await asyncio.to_thread(server_collector.get_realtime_stats)
    except Exception as e:
        print(f"Error in get_realtime_stats: {e}")
        return {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "disk_io": {"read_speed": 0, "write_speed": 0},
            "network_io": {"upload_speed": 0, "download_speed": 0},
            "network_total": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
            "disk_total": {"read_bytes": 0, "write_bytes": 0, "read_count": 0, "write_count": 0},
            "cpu_details": {"current_frequency": 0, "cpu_percent_per_core": []},
            "memory_details": {"total": 0, "available": 0, "used": 0, "free": 0},
            "system_load": {"load_1min": 0, "load_5min": 0, "load_15min": 0},
            "process_stats": {"total_processes": 0, "running_processes": 0, "sleeping_processes": 0},
            "process_info": {"total_processes": 0, "top_processes": [], "running_processes": 0, "sleeping_processes": 0},
            "network_interfaces": {},
            "network_connections": [],
            "timestamp": ""
        }


@router.get("/basic_info", response_model=BasicInfoSchema, summary="获取基础系统信息")
async def get_basic_info():
    """获取基础系统信息"""
    try:
        return await asyncio.to_thread(server_collector.get_basic_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/cpu_info", response_model=CpuInfoSchema, summary="获取CPU信息")
async def get_cpu_info():
    """获取CPU信息"""
    try:
        return await asyncio.to_thread(server_collector.get_cpu_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/memory_info", response_model=MemoryInfoSchema, summary="获取内存信息")
async def get_memory_info():
    """获取内存信息"""
    try:
        return await asyncio.to_thread(server_collector.get_memory_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/disk_info", response_model=DiskInfoSchema, summary="获取磁盘信息")
async def get_disk_info():
    """获取磁盘信息"""
    try:
        return await asyncio.to_thread(server_collector.get_disk_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/network_info", response_model=NetworkInfoSchema, summary="获取网络信息")
async def get_network_info():
    """获取网络信息"""
    try:
        return await asyncio.to_thread(server_collector.get_network_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/process_info", response_model=ProcessInfoSchema, summary="获取进程信息")
async def get_process_info():
    """获取进程信息"""
    try:
        return await asyncio.to_thread(server_collector.get_process_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/system_load", response_model=SystemLoadSchema, summary="获取系统负载信息")
async def get_system_load():
    """获取系统负载信息"""
    try:
        return await asyncio.to_thread(server_collector.get_system_load)
    except Exception as e:
        return {"error": str(e)}


@router.get("/boot_time", response_model=BootTimeSchema, summary="获取系统启动时间信息")
async def get_boot_time():
    """获取系统启动时间信息"""
    try:
        return await asyncio.to_thread(server_collector.get_boot_time)
    except Exception as e:
        return {"error": str(e)}


@router.get("/users_info", response_model=List[UserInfoSchema], summary="获取用户信息")
async def get_users_info():
    """获取用户信息"""
    try:
        return await asyncio.to_thread(server_collector.get_users_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/temperature_info", summary="获取温度信息")
async def get_temperature_info():
    """获取温度信息"""
    try:
        return await asyncio.to_thread(server_collector.get_temperature_info)
    except Exception as e:
        return {"error": str(e)}


@router.get("/battery_info", response_model=Optional[BatteryInfoSchema], summary="获取电池信息")
async def get_battery_info():
    """获取电池信息"""
    try:
        battery_info = await asyncio.to_thread(server_collector.get_battery_info)
        if battery_info:
            return battery_info
        else:
            return None
    except Exception as e:
        return {"error": str(e)}
