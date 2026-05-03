#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler Router - 定时任务模块路由
"""
from fastapi import APIRouter

from scheduler.api import router as scheduler_router

router = APIRouter()

# 注册调度器路由
router.include_router(scheduler_router)
