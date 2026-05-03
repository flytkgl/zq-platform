#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书同步 API - 组织架构与用户同步管理接口
"""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_schema import ResponseModel
from app.database import get_db
from core.feishu_sync.schema import (
    DeptTreeRequest,
    FeishuSyncConfigUpdate,
    TestConnectionRequest,
)
from core.feishu_sync.service import FeishuSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feishu-sync", tags=["飞书组织同步"])


@router.post("/test-connection", response_model=ResponseModel, summary="连接测试")
async def test_connection(data: TestConnectionRequest):
    try:
        result = await FeishuSyncService.test_connection(
            app_id=data.app_id,
            app_secret=data.app_secret,
        )
        return ResponseModel(data=result, message="连接成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)}")


@router.get("/config", summary="获取同步配置")
async def get_config():
    from core.system_config.service import SystemConfigService
    return await SystemConfigService.get_group_config("sync_feishu", mask_secrets=True)


@router.put("/config", response_model=ResponseModel, summary="保存同步配置")
async def update_config(
    data: FeishuSyncConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    from core.system_config.service import SystemConfigService
    configs = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = await SystemConfigService.update_group_config(db, "sync_feishu", configs)
    return ResponseModel(data=updated, message="保存成功")


@router.post("/sync/dept", response_model=ResponseModel, summary="同步组织架构")
async def sync_departments(db: AsyncSession = Depends(get_db)):
    try:
        result = await FeishuSyncService.sync_departments(db)
        return ResponseModel(data=result, message="组织架构同步完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"部门同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/sync/user", response_model=ResponseModel, summary="同步用户")
async def sync_users(db: AsyncSession = Depends(get_db)):
    try:
        result = await FeishuSyncService.sync_users(db)
        return ResponseModel(data=result, message="用户同步完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/stats", summary="获取同步统计")
async def get_sync_stats(db: AsyncSession = Depends(get_db)):
    stats = await FeishuSyncService.get_sync_stats(db)
    return stats


@router.get("/logs", summary="获取同步日志")
async def get_sync_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await FeishuSyncService.get_sync_logs(db, page=page, page_size=page_size)


@router.post("/dept-tree", summary="获取飞书部门树")
async def get_dept_tree(data: DeptTreeRequest):
    try:
        tree = await FeishuSyncService.get_feishu_dept_tree(
            app_id=data.app_id,
            app_secret=data.app_secret,
        )
        return tree
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取部门树失败: {str(e)}")


# ==================== 回调相关接口 ====================


@router.post("/callback", summary="飞书事件回调")
async def feishu_callback(request: Request):
    """
    飞书事件订阅回调端点（无需认证）

    处理两种场景：
    1. URL 验证: {"type":"url_verification","challenge":"xxx","token":"xxx"}
    2. 事件推送: {"encrypt":"xxx"} 或明文 v2.0 事件
    签名通过 Header: X-Lark-Signature, X-Lark-Request-Timestamp, X-Lark-Request-Nonce
    """
    from core.feishu_sync.callback_handler import FeishuCallbackHandler

    try:
        crypto = await FeishuCallbackHandler.get_crypto()
    except ValueError as e:
        logger.error(f"回调配置不完整: {e}")
        raise HTTPException(status_code=500, detail="回调配置不完整")

    raw_body = await request.body()
    body_str = raw_body.decode("utf-8")

    try:
        body = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 请求体")

    # URL 验证阶段飞书可能不带签名头，先尝试处理
    if body.get("type") == "url_verification":
        event_body = crypto.decrypt_event(body)
        return crypto.handle_url_verification(event_body)

    # 事件推送必须验证签名
    signature = request.headers.get("X-Lark-Signature", "")
    timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
    nonce = request.headers.get("X-Lark-Request-Nonce", "")

    if not all([signature, timestamp, nonce]):
        raise HTTPException(status_code=403, detail="缺少签名验证头")

    if not crypto.verify_signature(timestamp, nonce, body_str, signature):
        raise HTTPException(status_code=403, detail="签名验证失败")

    event_body = crypto.decrypt_event(body)

    event_type = event_body.get("header", {}).get("event_type", "")
    logger.info(f"收到飞书回调事件: {event_type}")

    asyncio.create_task(_safe_handle_event(event_body))

    return {"code": 0, "msg": "ok"}


async def _safe_handle_event(event_body: dict) -> None:
    """安全地处理回调事件"""
    from core.feishu_sync.callback_handler import FeishuCallbackHandler
    try:
        await FeishuCallbackHandler.handle_event(event_body)
    except Exception as e:
        logger.error(f"处理回调事件失败: {e}", exc_info=True)


@router.get("/callback/status", response_model=ResponseModel, summary="查询回调状态")
async def get_callback_status():
    try:
        result = await FeishuSyncService.get_callback_status()
        return ResponseModel(data=result, message="查询成功")
    except Exception as e:
        return ResponseModel(data={"registered": False}, message="未注册或查询失败")
