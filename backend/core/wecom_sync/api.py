#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业微信同步 API - 组织架构与用户同步管理接口
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_schema import ResponseModel
from app.database import get_db
from core.wecom_sync.schema import (
    DeptTreeRequest,
    TestConnectionRequest,
    WecomSyncConfigUpdate,
)
from core.wecom_sync.service import WecomSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wecom-sync", tags=["企业微信组织同步"])


@router.post("/test-connection", response_model=ResponseModel, summary="连接测试")
async def test_connection(data: TestConnectionRequest):
    try:
        result = await WecomSyncService.test_connection(
            corp_id=data.corp_id,
            corp_secret=data.corp_secret,
        )
        return ResponseModel(data=result, message="连接成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)}")


@router.get("/config", summary="获取同步配置")
async def get_config():
    from core.system_config.service import SystemConfigService
    return await SystemConfigService.get_group_config("sync_wecom", mask_secrets=True)


@router.put("/config", response_model=ResponseModel, summary="保存同步配置")
async def update_config(
    data: WecomSyncConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    from core.system_config.service import SystemConfigService
    configs = {k: v for k, v in data.model_dump().items() if v is not None}
    updated = await SystemConfigService.update_group_config(db, "sync_wecom", configs)
    return ResponseModel(data=updated, message="保存成功")


@router.post("/sync/dept", response_model=ResponseModel, summary="同步组织架构")
async def sync_departments(db: AsyncSession = Depends(get_db)):
    try:
        result = await WecomSyncService.sync_departments(db)
        return ResponseModel(data=result, message="组织架构同步完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"部门同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.post("/sync/user", response_model=ResponseModel, summary="同步用户")
async def sync_users(db: AsyncSession = Depends(get_db)):
    try:
        result = await WecomSyncService.sync_users(db)
        return ResponseModel(data=result, message="用户同步完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户同步失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@router.get("/stats", summary="获取同步统计")
async def get_sync_stats(db: AsyncSession = Depends(get_db)):
    stats = await WecomSyncService.get_sync_stats(db)
    return stats


@router.post("/dept-tree", summary="获取企业微信部门树")
async def get_dept_tree(data: DeptTreeRequest):
    try:
        tree = await WecomSyncService.get_wecom_dept_tree(
            corp_id=data.corp_id,
            corp_secret=data.corp_secret,
        )
        return tree
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取部门树失败: {str(e)}")


# ==================== 回调相关接口 ====================


@router.get("/callback", summary="企业微信回调URL验证")
async def wecom_callback_verify(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    """
    企业微信在配置回调URL时会发送 GET 请求验证URL有效性
    需要解密 echostr 并返回明文
    """
    from core.wecom_sync.callback_handler import WecomCallbackHandler

    try:
        crypto = await WecomCallbackHandler.get_crypto()
    except ValueError as e:
        logger.error(f"回调配置不完整: {e}")
        raise HTTPException(status_code=500, detail="回调配置不完整")

    try:
        reply_echostr = crypto.handle_verify(msg_signature, timestamp, nonce, echostr)
    except ValueError:
        raise HTTPException(status_code=403, detail="签名验证失败")

    return PlainTextResponse(content=reply_echostr)


@router.post("/callback", summary="企业微信事件回调")
async def wecom_callback(
    request: Request,
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
):
    """
    企业微信事件订阅回调端点（无需认证）

    企业微信通过 POST XML 推送事件变更
    """
    from core.wecom_sync.callback_handler import WecomCallbackHandler
    from xml.etree import ElementTree

    try:
        crypto = await WecomCallbackHandler.get_crypto()
    except ValueError as e:
        logger.error(f"回调配置不完整: {e}")
        raise HTTPException(status_code=500, detail="回调配置不完整")

    body = await request.body()
    post_data = body.decode("utf-8")

    try:
        plaintext = crypto.handle_callback(msg_signature, timestamp, nonce, post_data)
    except ValueError:
        raise HTTPException(status_code=403, detail="签名验证失败")

    # 解析 XML 事件内容
    root = ElementTree.fromstring(plaintext)
    event_type = ""
    change_type = ""

    event_node = root.find("Event")
    if event_node is not None:
        event_type = event_node.text or ""

    change_type_node = root.find("ChangeType")
    if change_type_node is not None:
        change_type = change_type_node.text or ""

    # 企业微信通讯录变更事件的 Event 为 "change_contact"，具体类型在 ChangeType 中
    actual_event = change_type if event_type == "change_contact" else event_type
    logger.info(f"收到企业微信回调事件: Event={event_type}, ChangeType={change_type}")

    # 提取事件数据
    event_data = {}
    for child in root:
        event_data[child.tag] = child.text

    if actual_event:
        asyncio.create_task(_safe_handle_event(actual_event, event_data))

    return PlainTextResponse(content=crypto.generate_success_response(), media_type="application/xml")


async def _safe_handle_event(event_type: str, event_data: dict) -> None:
    from core.wecom_sync.callback_handler import WecomCallbackHandler
    try:
        await WecomCallbackHandler.handle_event(event_type, event_data)
    except Exception as e:
        logger.error(f"处理回调事件失败 [{event_type}]: {e}", exc_info=True)


@router.get("/callback/status", response_model=ResponseModel, summary="查询回调状态")
async def get_callback_status():
    try:
        result = await WecomSyncService.get_callback_status()
        return ResponseModel(data=result, message="查询成功")
    except Exception as e:
        return ResponseModel(data={"registered": False}, message="查询失败")
