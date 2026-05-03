"""
zq_demo模块统一路由
"""
from fastapi import APIRouter

from zq_demo.api import router as demo_router

router = APIRouter()

# 注册子模块路由
router.include_router(demo_router, prefix="", tags=["Demo"])
