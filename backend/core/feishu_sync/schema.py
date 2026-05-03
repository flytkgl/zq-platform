#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书同步 Schema - 请求/响应模型
"""
from typing import List, Optional

from pydantic import BaseModel


class TestConnectionRequest(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None


class FeishuSyncConfigUpdate(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    sync_dept_id: Optional[str] = None
    sync_root_dept_id: Optional[str] = None
    enable_dept_event: Optional[str] = None
    enable_user_event: Optional[str] = None
    encrypt_key: Optional[str] = None
    verification_token: Optional[str] = None
    callback_url: Optional[str] = None


class DeptTreeRequest(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None


class FeishuDeptTreeNode(BaseModel):
    dept_id: str
    name: str
    children: List["FeishuDeptTreeNode"] = []
