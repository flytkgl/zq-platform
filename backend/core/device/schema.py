#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设备管理 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.base_schema import CSTDatetime


class DeviceInfo(BaseModel):
    """设备信息"""
    device_id: str = Field(..., description="设备唯一标识")
    device_name: Optional[str] = Field(None, description="自定义设备名称")
    device_type: Optional[str] = Field(None, description="设备类型(desktop/mobile/tablet)")
    browser_type: Optional[str] = Field(None, description="浏览器类型")
    os_type: Optional[str] = Field(None, description="操作系统类型")
    ip_address: Optional[str] = Field(None, description="IP地址")
    last_active_time: Optional[CSTDatetime] = Field(None, description="最后活跃时间")
    is_current: bool = Field(False, description="是否当前设备")
    is_online: bool = Field(False, description="是否在线")


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    current_device: Optional[DeviceInfo] = Field(None, description="当前设备")
    online_devices: list[DeviceInfo] = Field(default_factory=list, description="在线设备列表")
    total_count: int = Field(0, description="设备总数")


class DeviceRenameRequest(BaseModel):
    """设备重命名请求"""
    device_name: str = Field(..., min_length=1, max_length=50, description="设备名称")
