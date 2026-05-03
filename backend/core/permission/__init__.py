#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Permission Module - 权限管理模块
"""
from core.permission.model import Permission
from core.permission.service import PermissionService
from core.permission.api import router

__all__ = ["Permission", "PermissionService", "router"]
