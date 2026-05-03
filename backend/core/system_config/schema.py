#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SystemConfig Schema - 系统配置 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict


class SystemConfigBase(BaseModel):
    """基础 Schema"""
    config_group: str
    config_key: str
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_secret: bool = False
    status: bool = True


class SystemConfigCreate(SystemConfigBase):
    """创建 Schema"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新 Schema"""
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_secret: Optional[bool] = None
    status: Optional[bool] = None


class SystemConfigResponse(SystemConfigBase):
    """响应 Schema"""
    id: str
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[datetime] = None
    sys_update_datetime: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GroupConfigUpdate(BaseModel):
    """按分组批量更新配置"""
    configs: Dict[str, Optional[str]]


class GroupConfigResponse(BaseModel):
    """按分组返回配置（敏感字段脱敏）"""
    group: str
    configs: Dict[str, Any]
