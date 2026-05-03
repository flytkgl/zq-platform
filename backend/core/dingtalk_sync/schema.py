#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉同步 Schema - 请求/响应模型
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TestConnectionRequest(BaseModel):
    app_key: Optional[str] = None
    app_secret: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    corp_name: Optional[str] = None
    dept_id: Optional[int] = None
    message: Optional[str] = None


class DingtalkSyncConfigUpdate(BaseModel):
    corp_id: Optional[str] = None
    app_key: Optional[str] = None
    app_secret: Optional[str] = None
    sync_dept_id: Optional[str] = None
    sync_root_dept_id: Optional[str] = None
    enable_dept_event: Optional[str] = None
    enable_user_event: Optional[str] = None
    callback_token: Optional[str] = None
    callback_aes_key: Optional[str] = None
    callback_url: Optional[str] = None


class SyncTypeStats(BaseModel):
    total_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    not_synced: int = 0
    status: Optional[str] = None
    sync_time: Optional[str] = None


class SyncStatsResponse(BaseModel):
    dept: SyncTypeStats
    user: SyncTypeStats


class SyncLogItem(BaseModel):
    id: str
    sync_type: str
    total_count: Optional[int] = 0
    success_count: Optional[int] = 0
    fail_count: Optional[int] = 0
    status: Optional[str] = None
    error_detail: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class SyncLogListResponse(BaseModel):
    items: List[SyncLogItem]
    total: int
    page: int
    page_size: int


class DingtalkDeptTreeNode(BaseModel):
    dept_id: int
    name: str
    children: List["DingtalkDeptTreeNode"] = []


class DeptTreeRequest(BaseModel):
    app_key: Optional[str] = None
    app_secret: Optional[str] = None
