#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Role Module - 角色管理模块
"""
from core.role.model import Role
from core.role.service import RoleService
from core.role.api import router

__all__ = ["Role", "RoleService", "router"]
