#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业微信同步 Schema - 请求/响应模型
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TestConnectionRequest(BaseModel):
    corp_id: Optional[str] = None
    corp_secret: Optional[str] = None


class WecomSyncConfigUpdate(BaseModel):
    corp_id: Optional[str] = None
    corp_secret: Optional[str] = None
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


class WecomDeptTreeNode(BaseModel):
    dept_id: int
    name: str
    children: List["WecomDeptTreeNode"] = []


class DeptTreeRequest(BaseModel):
    corp_id: Optional[str] = None
    corp_secret: Optional[str] = None
