#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉同步 API - 组织架构与用户同步管理接口
"""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_schema import ResponseModel
from app.database import get_db
from core.dingtalk_sync.schema import (
    DeptTreeRequest,
    DingtalkSyncConfigUpdate,
    TestConnectionRequest,
)
from core.dingtalk_sync.service import DingtalkSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dingtalk-sync", tags=["钉钉组织同步"])


@router.post("/test-connection", response_model=ResponseModel, summary="连接测试")
async def test_connection(data: TestConnectionRequest):
    """
    测试钉钉连接
    可传入临时凭证（保存前测试），不传则使用已保存配置
    """
    try:
        result = await DingtalkSyncService.test_connection(
            app_key=data.app_key,
            app_secret=data.app_secret,
        )
        return ResponseModel(data=result, message="连接成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)}")


@router.get("/config", summary="获取同步配置")
async def get_config():
    """获取钉钉同步配置（敏感字段脱敏）"""
    from core.system_config.service import SystemConfigService
    return await SystemConfigService.get_group_config("sync_dingtalk", mask_secrets=True)


@router.put("/config", response_model=ResponseModel, summary="保存同步配置")
async def update_config(
    data: DingtalkSyncConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """保存钉钉同步配置"""
    from core.system_config.service import SystemConfigService
    configs = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = await SystemConfigService.update_group_config(db, "sync_dingtalk", configs)
    return ResponseModel(data=updated, message="保存成功")


@router.post("/sync/dept", response_model=ResponseModel, summary="同步组织架构")
async def sync_departments(db: AsyncSession = Depends(get_db)):
    """手动触发部门同步"""
    try:
        result = await DingtalkSyncService.sync_departments(db)
        return ResponseModel(data=result, message="组织架构同步完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"部门同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/sync/user", response_model=ResponseModel, summary="同步用户")
async def sync_users(db: AsyncSession = Depends(get_db)):
    """手动触发用户同步"""
    try:
        result = await DingtalkSyncService.sync_users(db)
        return ResponseModel(data=result, message="用户同步完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/stats", summary="获取同步统计")
async def get_sync_stats(db: AsyncSession = Depends(get_db)):
    """获取最新的部门/用户同步统计数据"""
    stats = await DingtalkSyncService.get_sync_stats(db)
    return stats


@router.get("/logs", summary="获取同步日志")
async def get_sync_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取同步日志列表"""
    return await DingtalkSyncService.get_sync_logs(db, page=page, page_size=page_size)


@router.post("/dept-tree", summary="获取钉钉部门树")
async def get_dept_tree(data: DeptTreeRequest):
    """
    从钉钉拉取部门树（用于选择同步范围）
    可传入临时凭证，不传则使用已保存配置
    """
    try:
        tree = await DingtalkSyncService.get_dingtalk_dept_tree(
            app_key=data.app_key,
            app_secret=data.app_secret,
        )
        return tree
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取部门树失败: {str(e)}")


# ==================== 回调相关接口 ====================


@router.post("/callback", summary="钉钉事件回调")
async def dingtalk_callback(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(..., alias="timestamp"),
    nonce: str = Query(..., alias="nonce"),
):
    """
    钉钉事件订阅回调端点（无需认证）

    钉钉在注册回调时、以及每次事件推送时都会 POST 到这个地址。
    请求体: {"encrypt": "..."}
    Query params: msg_signature, timestamp, nonce
    """
    from core.dingtalk_sync.callback_handler import DingtalkCallbackHandler

    try:
        crypto = await DingtalkCallbackHandler.get_crypto()
    except ValueError as e:
        logger.error(f"回调配置不完整: {e}")
        raise HTTPException(status_code=500, detail="回调配置不完整")

    body = await request.json()
    encrypt = body.get("encrypt", "")
    if not encrypt:
        raise HTTPException(status_code=400, detail="缺少 encrypt 字段")

    try:
        plaintext = crypto.handle_callback(msg_signature, timestamp, nonce, encrypt)
    except ValueError:
        raise HTTPException(status_code=403, detail="签名验证失败")

    event_data = json.loads(plaintext)
    event_type = event_data.get("EventType", "")
    logger.info(f"收到钉钉回调事件: {event_type}")

    # 异步处理事件（不阻塞响应）
    if event_type != "check_url":
        asyncio.create_task(_safe_handle_event(event_type, event_data))

    return crypto.generate_success_response()


async def _safe_handle_event(event_type: str, event_data: dict) -> None:
    """安全地处理回调事件，捕获异常避免任务崩溃"""
    from core.dingtalk_sync.callback_handler import DingtalkCallbackHandler
    try:
        await DingtalkCallbackHandler.handle_event(event_type, event_data)
    except Exception as e:
        logger.error(f"处理回调事件失败 [{event_type}]: {e}", exc_info=True)


@router.post("/callback/register", response_model=ResponseModel, summary="注册事件回调")
async def register_callback():
    """
    向钉钉注册回调地址，订阅通讯录变更事件

    需要先在配置中填写 callback_token 和 callback_aes_key
    """
    try:
        result = await DingtalkSyncService.register_callback()
        return ResponseModel(data=result, message="注册回调成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"注册回调失败: {e}")
        raise HTTPException(status_code=500, detail=f"注册回调失败: {str(e)}")


@router.delete("/callback/register", response_model=ResponseModel, summary="删除事件回调")
async def delete_callback():
    """删除已注册的钉钉事件回调"""
    try:
        await DingtalkSyncService.delete_callback()
        return ResponseModel(message="删除回调成功")
    except Exception as e:
        logger.error(f"删除回调失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除回调失败: {str(e)}")


@router.get("/callback/status", response_model=ResponseModel, summary="查询回调状态")
async def get_callback_status():
    """查询当前钉钉回调注册状态"""
    try:
        result = await DingtalkSyncService.get_callback_status()
        return ResponseModel(data=result, message="查询成功")
    except Exception as e:
        return ResponseModel(data={"registered": False}, message="未注册或查询失败")
