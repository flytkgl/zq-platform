#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用管理Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field

from app.base_schema import CSTDatetime


class ApplicationBase(BaseModel):
    """应用基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="应用名称")
    code: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", description="应用编码")
    description: Optional[str] = Field(default="", description="应用描述")
    icon: Optional[str] = Field(default="", description="应用图标")
    cover: Optional[str] = Field(default="", description="应用封面图URL")
    app_type: Optional[str] = Field(default="mixed", description="应用类型: form/workflow/dashboard/screen/mixed/ai")
    home_path: Optional[str] = Field(default=None, description="应用首页路径")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="应用配置")
    system_menu_ids: Optional[List[str]] = Field(default_factory=list, description="开发模式下显示的系统菜单ID列表")


class ApplicationCreate(ApplicationBase):
    """创建应用Schema"""
    pass


class ApplicationUpdate(BaseModel):
    """更新应用Schema - 所有字段可选"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="应用名称")
    code: Optional[str] = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", description="应用编码")
    description: Optional[str] = Field(default=None, description="应用描述")
    icon: Optional[str] = Field(default=None, description="应用图标")
    cover: Optional[str] = Field(default=None, description="应用封面图URL")
    app_type: Optional[str] = Field(default=None, description="应用类型")
    home_path: Optional[str] = Field(default=None, description="应用首页路径")
    status: Optional[str] = Field(default=None, description="应用状态: draft/published/disabled")
    config: Optional[Dict[str, Any]] = Field(default=None, description="应用配置")
    team_ids: Optional[List[str]] = Field(default=None, description="团队成员ID列表")
    system_menu_ids: Optional[List[str]] = Field(default=None, description="开发模式下显示的系统菜单ID列表")


class ApplicationResponse(ApplicationBase):
    """应用响应Schema"""
    id: str
    status: str = "draft"
    home_path: Optional[str] = None
    version: int = 1
    owner_id: Optional[str] = None
    team_ids: List[str] = []
    system_menu_ids: Optional[List[str]] = []
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    """应用列表响应Schema（简化版）"""
    id: str
    name: str
    code: str
    description: Optional[str] = ""
    icon: Optional[str] = ""
    cover: Optional[str] = ""
    app_type: str = "mixed"
    status: str = "draft"
    home_path: Optional[str] = None
    version: int = 1
    owner_id: Optional[str] = None
    system_menu_ids: Optional[List[str]] = []
    sys_create_datetime: Optional[CSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatsResponse(BaseModel):
    """应用统计响应Schema"""
    id: str
    name: str
    code: str
    form_count: int = 0
    page_count: int = 0
    workflow_count: int = 0
    screen_count: int = 0
    data_source_count: int = 0
