#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件管理路由
"""
from fastapi import APIRouter

from core.file_manager.api import router as file_manager_router
from core.file_manager.chunk_upload_api import router as chunk_upload_router

router = APIRouter()

router.include_router(file_manager_router)
router.include_router(chunk_upload_router)
