#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消息中心 API（异步版本）
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import PaginatedResponse, ResponseModel
from core.message.schema import (
    MessageOut,
    MessageListOut,
    UnreadCountOut,
    MarkReadInput,
    SendMessageInput,
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementOut,
    AnnouncementListOut,
    UserAnnouncementOut,
    ReadStatsOut,
    EmailTestInput,
    EmailSendInput,
    DingTalkWebhookTestInput,
    DingTalkWorkNoticeTestInput,
    FeishuWebhookTestInput,
    FeishuAppMessageTestInput,
    WecomWebhookTestInput,
    WecomAppMessageTestInput,
    WechatMPTestInput,
)
from core.message.service import MessageService, AnnouncementService, NotifyService

router = APIRouter(prefix="/message", tags=["消息中心"])


# ============ 消息 API ============

@router.get("/list", response_model=PaginatedResponse[MessageListOut], summary="消息列表")
async def list_messages(
        request: Request,
        msg_type: str = Query(None, description="消息类型"),
        status: str = Query(None, description="状态: unread/read"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取当前用户的消息列表"""
    user_id = request.state.user_id
    items, total = await MessageService.get_list(
        db=db,
        user_id=user_id,
        msg_type=msg_type,
        status=status,
        page=page,
        page_size=page_size,
    )

    # 批量获取发送人名称
    sender_ids = list(set(str(item.sender_id) for item in items if item.sender_id))
    sender_names = await _batch_get_user_names(db, sender_ids) if sender_ids else {}

    return PaginatedResponse(
        items=[
            _build_message_list_out(item, sender_names.get(str(item.sender_id), "") if item.sender_id else "")
            for item in items
        ],
        total=total,
    )


@router.get("/unread-count", response_model=UnreadCountOut, summary="未读数量")
async def get_unread_count(
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """获取未读消息数量"""
    user_id = request.state.user_id
    total = await MessageService.get_unread_count(db, user_id)
    by_type = await MessageService.get_unread_count_by_type(db, user_id)

    return UnreadCountOut(total=total, by_type=by_type)


@router.post("/read-all", response_model=ResponseModel, summary="全部已读")
async def mark_all_as_read(
        request: Request,
        data: MarkReadInput = None,
        db: AsyncSession = Depends(get_db),
):
    """标记所有消息为已读"""
    user_id = request.state.user_id
    msg_type = data.msg_type if data else None
    count = await MessageService.mark_all_as_read(db, user_id, msg_type)

    return ResponseModel(message=f"已标记 {count} 条消息为已读")


@router.delete("/clear-read", response_model=ResponseModel, summary="清空已读")
async def clear_read_messages(
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """清空所有已读消息"""
    user_id = request.state.user_id
    count = await MessageService.delete_all_read(db, user_id)

    return ResponseModel(message=f"已删除 {count} 条已读消息")


@router.get("/{message_id}", response_model=MessageOut, summary="消息详情")
async def get_message(
        request: Request,
        message_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取消息详情"""
    user_id = request.state.user_id
    message = await MessageService.get_by_id(db, message_id, user_id)
    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    return await _build_message_out(db, message)


@router.post("/{message_id}/read", response_model=ResponseModel, summary="标记已读")
async def mark_as_read(
        request: Request,
        message_id: str,
        db: AsyncSession = Depends(get_db),
):
    """标记单条消息为已读"""
    user_id = request.state.user_id
    success = await MessageService.mark_as_read(db, message_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")

    return ResponseModel(message="已标记为已读")


@router.delete("/{message_id}", response_model=ResponseModel, summary="删除消息")
async def delete_message(
        request: Request,
        message_id: str,
        db: AsyncSession = Depends(get_db),
):
    """删除单条消息"""
    user_id = request.state.user_id
    success = await MessageService.delete(db, message_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="消息不存在")

    return ResponseModel(message="删除成功")


@router.post("/send", response_model=ResponseModel, summary="发送消息")
async def send_message(
        request: Request,
        data: SendMessageInput,
        db: AsyncSession = Depends(get_db),
):
    """发送站内消息（支持多渠道）"""
    sender_id = request.state.user_id

    if not data.recipient_ids:
        raise HTTPException(status_code=400, detail="接收人不能为空")
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="消息标题不能为空")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    results = await NotifyService.send(
        db=db,
        recipient_ids=data.recipient_ids,
        title=data.title,
        content=data.content,
        channels=data.channels,
        msg_type=data.msg_type,
        sender_id=sender_id,
    )

    return ResponseModel(
        message=f"消息已发送给 {len(data.recipient_ids)} 人",
        data={"results": results, "recipient_count": len(data.recipient_ids)},
    )


# ============ 公告管理端 API ============

announcement_router = APIRouter(prefix="/announcement", tags=["公告管理"])


@announcement_router.get("/admin/list", response_model=PaginatedResponse[AnnouncementListOut], summary="公告列表（管理）")
async def list_announcements(
        status: str = Query(None, description="状态: draft/published/expired"),
        keyword: str = Query(None, description="关键词搜索"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取公告列表（管理端）"""
    items, total = await AnnouncementService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
    )

    # 批量查询发布人名称
    publisher_names = await _batch_get_user_names(db, [a.publisher_id for a in items if a.publisher_id])

    return PaginatedResponse(
        items=[_build_announcement_list_out(item, publisher_names) for item in items],
        total=total,
    )


@announcement_router.get("/admin/{announcement_id}", response_model=AnnouncementOut, summary="公告详情（管理）")
async def get_announcement(
        announcement_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取公告详情"""
    announcement = await AnnouncementService.get_by_id(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    return await _build_announcement_out(db, announcement)


@announcement_router.post("/admin", response_model=AnnouncementOut, summary="创建公告")
async def create_announcement(
        request: Request,
        data: AnnouncementCreate,
        db: AsyncSession = Depends(get_db),
):
    """创建公告"""
    user_id = request.state.user_id
    announcement = await AnnouncementService.create(db, data.model_dump(), user_id)
    return await _build_announcement_out(db, announcement)


@announcement_router.put("/admin/{announcement_id}", response_model=AnnouncementOut, summary="更新公告")
async def update_announcement(
        request: Request,
        announcement_id: str,
        data: AnnouncementUpdate,
        db: AsyncSession = Depends(get_db),
):
    """更新公告"""
    user_id = request.state.user_id
    announcement = await AnnouncementService.update(
        db, announcement_id, data.model_dump(exclude_unset=True), user_id
    )
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    return await _build_announcement_out(db, announcement)


@announcement_router.delete("/admin/{announcement_id}", response_model=ResponseModel, summary="删除公告")
async def delete_announcement(
        request: Request,
        announcement_id: str,
        db: AsyncSession = Depends(get_db),
):
    """删除公告"""
    user_id = request.state.user_id
    success = await AnnouncementService.delete(db, announcement_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")

    return ResponseModel(message="删除成功")


@announcement_router.post("/admin/{announcement_id}/publish", response_model=AnnouncementOut, summary="发布公告")
async def publish_announcement(
        request: Request,
        announcement_id: str,
        db: AsyncSession = Depends(get_db),
):
    """发布公告"""
    user_id = request.state.user_id
    try:
        announcement = await AnnouncementService.publish(db, announcement_id, user_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="公告不存在")
        return await _build_announcement_out(db, announcement)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@announcement_router.get("/admin/{announcement_id}/stats", response_model=ReadStatsOut, summary="阅读统计")
async def get_read_stats(
        announcement_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取公告阅读统计"""
    stats = await AnnouncementService.get_read_stats(db, announcement_id)
    if not stats:
        raise HTTPException(status_code=404, detail="公告不存在")

    return ReadStatsOut(**stats)


# ============ 公告用户端 API ============

@announcement_router.get("/user/list", response_model=PaginatedResponse[UserAnnouncementOut], summary="我的公告")
async def list_user_announcements(
        request: Request,
        unread_only: bool = Query(False, description="只看未读"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取当前用户可见的公告列表"""
    user_id = request.state.user_id
    # 从token中获取用户的部门和角色信息
    user_dept_ids = []
    user_role_ids = []
    if hasattr(request.state, 'token_payload'):
        payload = request.state.token_payload
        if payload.get('dept_id'):
            user_dept_ids = [payload.get('dept_id')]
        if payload.get('role_id'):
            user_role_ids = [payload.get('role_id')]

    items, total = await AnnouncementService.get_user_announcements(
        db=db,
        user_id=user_id,
        user_dept_ids=user_dept_ids,
        user_role_ids=user_role_ids,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )

    # 批量查询发布人名称
    publisher_names = await _batch_get_user_names(db, [a.publisher_id for a in items if a.publisher_id])

    return PaginatedResponse(
        items=[_build_user_announcement_out(item, publisher_names) for item in items],
        total=total,
    )


@announcement_router.get("/user/unread-count", response_model=dict, summary="未读公告数量")
async def get_user_unread_count(
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """获取未读公告数量"""
    user_id = request.state.user_id
    user_dept_ids = []
    user_role_ids = []
    if hasattr(request.state, 'token_payload'):
        payload = request.state.token_payload
        if payload.get('dept_id'):
            user_dept_ids = [payload.get('dept_id')]
        if payload.get('role_id'):
            user_role_ids = [payload.get('role_id')]

    count = await AnnouncementService.get_unread_count(
        db, user_id, user_dept_ids, user_role_ids
    )
    return {"count": count}


@announcement_router.get("/user/{announcement_id}", response_model=UserAnnouncementOut, summary="公告详情")
async def get_user_announcement(
        request: Request,
        announcement_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取公告详情并标记已读"""
    user_id = request.state.user_id
    announcement = await AnnouncementService.get_by_id(db, announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    # 标记已读
    await AnnouncementService.mark_as_read(db, announcement_id, user_id)

    # 重新获取以更新is_read状态
    announcement.is_read = True

    publisher_names = await _batch_get_user_names(db, [announcement.publisher_id] if announcement.publisher_id else [])
    return _build_user_announcement_out(announcement, publisher_names)


@announcement_router.post("/user/{announcement_id}/read", response_model=ResponseModel, summary="标记已读")
async def mark_announcement_as_read(
        request: Request,
        announcement_id: str,
        db: AsyncSession = Depends(get_db),
):
    """标记公告为已读"""
    user_id = request.state.user_id
    success = await AnnouncementService.mark_as_read(db, announcement_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")

    return ResponseModel(message="已标记为已读")


# ============ 辅助函数 ============

async def _batch_get_user_names(db: AsyncSession, user_ids: list) -> Dict[str, str]:
    """批量查询用户名称，返回 {user_id: name} 映射"""
    if not user_ids:
        return {}
    from core.user.model import User
    from sqlalchemy import select
    unique_ids = list(set(str(uid) for uid in user_ids))
    stmt = select(User.id, User.name).where(User.id.in_(unique_ids))
    result = await db.execute(stmt)
    return {str(row[0]): row[1] or "" for row in result.all()}


async def _build_message_out(db: AsyncSession, message) -> dict:
    """构建消息详情输出"""
    sender_name = ""
    if message.sender_id:
        sender_names = await _batch_get_user_names(db, [message.sender_id])
        sender_name = sender_names.get(str(message.sender_id), "")

    return {
        "id": str(message.id),
        "title": message.title,
        "content": message.content,
        "msg_type": message.msg_type,
        "status": message.status,
        "link_type": message.link_type or "",
        "link_id": message.link_id or "",
        "sender_name": sender_name,
        "read_at": message.read_at,
        "created_at": message.sys_create_datetime,
    }


def _build_message_list_out(message, sender_name: str = "") -> dict:
    """构建消息列表输出"""
    return {
        "id": str(message.id),
        "title": message.title,
        "content": message.content[:100] if message.content else "",
        "msg_type": message.msg_type,
        "status": message.status,
        "link_type": message.link_type or "",
        "link_id": message.link_id or "",
        "sender_id": str(message.sender_id) if message.sender_id else None,
        "sender_name": sender_name,
        "created_at": message.sys_create_datetime,
    }


async def _build_announcement_out(db: AsyncSession, announcement) -> dict:
    """构建公告输出"""
    publisher_name = ""
    if announcement.publisher_id:
        from core.user.model import User
        from sqlalchemy import select
        stmt = select(User).where(User.id == announcement.publisher_id)
        result = await db.execute(stmt)
        publisher = result.scalar_one_or_none()
        if publisher:
            publisher_name = publisher.name or ""

    return {
        "id": str(announcement.id),
        "title": announcement.title,
        "content": announcement.content,
        "summary": announcement.summary or "",
        "status": announcement.status,
        "priority": announcement.priority,
        "is_top": announcement.is_top,
        "target_type": announcement.target_type,
        "target_ids": announcement.target_ids or [],
        "publish_time": announcement.publish_time,
        "expire_time": announcement.expire_time,
        "publisher_id": str(announcement.publisher_id) if announcement.publisher_id else None,
        "publisher_name": publisher_name,
        "read_count": announcement.read_count or 0,
        "created_at": announcement.sys_create_datetime,
    }


def _build_announcement_list_out(announcement, publisher_names: Dict[str, str] = None) -> dict:
    """构建公告列表输出"""
    publisher_name = ""
    if publisher_names and announcement.publisher_id:
        publisher_name = publisher_names.get(str(announcement.publisher_id), "")
    return {
        "id": str(announcement.id),
        "title": announcement.title,
        "summary": announcement.summary or "",
        "status": announcement.status,
        "priority": announcement.priority,
        "is_top": announcement.is_top,
        "target_type": announcement.target_type,
        "publisher_name": publisher_name,
        "read_count": announcement.read_count or 0,
        "publish_time": announcement.publish_time,
        "created_at": announcement.sys_create_datetime,
    }


def _build_user_announcement_out(announcement, publisher_names: Dict[str, str] = None) -> dict:
    """构建用户公告输出"""
    publisher_name = ""
    if publisher_names and announcement.publisher_id:
        publisher_name = publisher_names.get(str(announcement.publisher_id), "")
    return {
        "id": str(announcement.id),
        "title": announcement.title,
        "summary": announcement.summary or "",
        "content": announcement.content,
        "priority": announcement.priority,
        "is_top": announcement.is_top,
        "is_read": getattr(announcement, "is_read", False),
        "publisher_name": publisher_name,
        "publish_time": announcement.publish_time,
    }


# ============ 邮件 API ============

@router.get("/email/status", response_model=ResponseModel, summary="邮件配置状态")
async def email_status():
    """查看 SMTP 邮件配置状态（通过 config_manager 三级获取）"""
    from app.email import EmailSender

    config = await EmailSender._get_smtp_config()
    configured = bool(config["host"] and config["user"] and config["password"])
    return ResponseModel(
        message="SMTP 已配置" if configured else "SMTP 未配置",
        data={
            "configured": configured,
            "smtp_host": config["host"] or "",
            "smtp_port": config["port"],
            "smtp_user": config["user"][:3] + "***" if config["user"] else "",
            "smtp_use_tls": config["use_tls"],
            "from_name": config["from_name"] or "",
            "from_email": config["from_email"] or "",
        },
    )


@router.post("/email/test", response_model=ResponseModel, summary="测试邮件发送")
async def email_test(data: EmailTestInput):
    """发送测试邮件以验证 SMTP 配置"""
    from app.email import EmailSender

    if not await EmailSender.is_configured_async():
        raise HTTPException(status_code=400, detail="SMTP 未配置，请先在系统配置中配置邮箱相关参数")

    html_content = EmailSender.build_notification_html(
        title="测试邮件",
        content="这是一封测试邮件，用于验证 SMTP 配置是否正确。如果您收到了这封邮件，说明邮件推送功能已正常工作。",
    )
    success = await EmailSender.send(
        to_email=data.to_email,
        subject="[测试] 邮件推送配置验证",
        content=html_content,
        html=True,
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败，请检查 SMTP 配置")

    return ResponseModel(message="测试邮件发送成功")


@router.post("/email/send", response_model=ResponseModel, summary="发送邮件通知")
async def email_send(data: EmailSendInput, db: AsyncSession = Depends(get_db)):
    """手动向指定用户发送邮件通知"""
    from core.message.service import NotifyService

    result = await NotifyService._send_email(
        db=db,
        recipient_ids=data.recipient_ids,
        title=data.title,
        content=data.content,
    )

    return ResponseModel(
        message="邮件发送成功" if result else "部分或全部邮件发送失败",
        data={"success": result},
    )


# ============ 钉钉通知 API ============

@router.get("/dingtalk/status", response_model=ResponseModel, summary="钉钉通知配置状态")
async def dingtalk_status():
    """查看钉钉通知配置状态（通过 config_manager 三级获取）"""
    from app.dingtalk import DingTalkWebhook, DingTalkWorkNotice
    from app.config_manager import config_manager

    notify_config = await config_manager.get_group("notify_dingtalk")
    oauth_config = await config_manager.get_group("oauth_dingtalk")

    webhook_url = notify_config.get("webhook_url") or ""
    webhook_secret = notify_config.get("webhook_secret") or ""
    agent_id = notify_config.get("agent_id") or ""
    app_id = oauth_config.get("app_id") or ""
    app_secret = oauth_config.get("app_secret") or ""

    return ResponseModel(
        message="钉钉通知配置状态",
        data={
            "webhook": {
                "configured": bool(webhook_url),
                "url": (webhook_url[:30] + "***") if webhook_url else "",
                "has_secret": bool(webhook_secret),
            },
            "work_notice": {
                "configured": bool(app_id and app_secret and agent_id),
                "agent_id": agent_id,
                "app_id": (app_id[:4] + "***") if app_id else "",
            },
        },
    )


@router.post("/dingtalk/webhook/test", response_model=ResponseModel, summary="测试钉钉 Webhook")
async def dingtalk_webhook_test(data: DingTalkWebhookTestInput):
    """发送测试消息到钉钉群机器人"""
    from app.dingtalk import DingTalkWebhook

    if not await DingTalkWebhook.is_configured_async():
        raise HTTPException(status_code=400, detail="钉钉 Webhook 未配置")

    success = await DingTalkWebhook.send_text(content=f"[测试] {data.content}")
    if not success:
        raise HTTPException(status_code=500, detail="钉钉 Webhook 发送失败")

    return ResponseModel(message="钉钉 Webhook 测试消息发送成功")


@router.post("/dingtalk/work-notice/test", response_model=ResponseModel, summary="测试钉钉工作通知")
async def dingtalk_work_notice_test(data: DingTalkWorkNoticeTestInput, db: AsyncSession = Depends(get_db)):
    """发送测试工作通知到指定用户"""
    from app.dingtalk import DingTalkWorkNotice
    from core.message.service import NotifyService

    if not await DingTalkWorkNotice.is_configured_async():
        raise HTTPException(status_code=400, detail="钉钉工作通知未配置，需要配置钉钉 OAuth 应用及 agent_id")

    # 查询用户的钉钉 unionId
    from core.user.model import User
    from sqlalchemy import select
    stmt = select(User.dingtalk_unionid, User.name).where(User.id == data.user_id)
    result = await db.execute(stmt)
    row = result.first()

    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="该用户未绑定钉钉账号")

    # unionId 转 userId
    user_ids = await NotifyService._convert_dingtalk_unionids([row[0]])
    if not user_ids:
        raise HTTPException(status_code=500, detail="钉钉 unionId 转 userId 失败")

    success = await DingTalkWorkNotice.send_text(
        userid_list=user_ids,
        content=f"[测试] 这是一条发送给 {row[1] or '用户'} 的测试工作通知",
    )
    if not success:
        raise HTTPException(status_code=500, detail="钉钉工作通知发送失败")

    return ResponseModel(message="钉钉工作通知测试发送成功")


# ============ 飞书通知 API ============

@router.get("/feishu/status", response_model=ResponseModel, summary="飞书通知配置状态")
async def feishu_status():
    """查看飞书通知配置状态（通过 config_manager 三级获取）"""
    from app.config_manager import config_manager

    notify_config = await config_manager.get_group("notify_feishu")
    oauth_config = await config_manager.get_group("oauth_feishu")

    webhook_url = notify_config.get("webhook_url") or ""
    webhook_secret = notify_config.get("webhook_secret") or ""
    app_id = oauth_config.get("app_id") or ""
    app_secret = oauth_config.get("app_secret") or ""

    return ResponseModel(
        message="飞书通知配置状态",
        data={
            "webhook": {
                "configured": bool(webhook_url),
                "url": (webhook_url[:30] + "***") if webhook_url else "",
                "has_secret": bool(webhook_secret),
            },
            "app_message": {
                "configured": bool(app_id and app_secret),
                "app_id": (app_id[:4] + "***") if app_id else "",
            },
        },
    )


@router.post("/feishu/webhook/test", response_model=ResponseModel, summary="测试飞书 Webhook")
async def feishu_webhook_test(data: FeishuWebhookTestInput):
    """发送测试消息到飞书群机器人"""
    from app.feishu import FeishuWebhook

    if not await FeishuWebhook.is_configured_async():
        raise HTTPException(status_code=400, detail="飞书 Webhook 未配置")

    success = await FeishuWebhook.send_text(text=f"[测试] {data.content}")
    if not success:
        raise HTTPException(status_code=500, detail="飞书 Webhook 发送失败")

    return ResponseModel(message="飞书 Webhook 测试消息发送成功")


@router.post("/feishu/app-message/test", response_model=ResponseModel, summary="测试飞书应用消息")
async def feishu_app_message_test(data: FeishuAppMessageTestInput, db: AsyncSession = Depends(get_db)):
    """发送测试应用消息到指定用户"""
    from app.feishu import FeishuAppMessage

    if not await FeishuAppMessage.is_configured_async():
        raise HTTPException(status_code=400, detail="飞书应用消息未配置，需要配置飞书 OAuth 应用")

    # 查询用户的飞书 union_id
    from core.user.model import User
    from sqlalchemy import select
    stmt = select(User.feishu_union_id, User.name).where(User.id == data.user_id)
    result = await db.execute(stmt)
    row = result.first()

    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="该用户未绑定飞书账号")

    # union_id 转 open_id
    id_map = await FeishuAppMessage.get_open_ids_by_union_ids([row[0]])
    open_id = id_map.get(row[0])
    if not open_id:
        raise HTTPException(status_code=500, detail="飞书 union_id 转 open_id 失败")

    success = await FeishuAppMessage.send_text(
        open_id=open_id,
        text=f"[测试] 这是一条发送给 {row[1] or '用户'} 的测试消息",
    )
    if not success:
        raise HTTPException(status_code=500, detail="飞书应用消息发送失败")

    return ResponseModel(message="飞书应用消息测试发送成功")


# ============ 企业微信通知 API ============

@router.get("/wecom/status", response_model=ResponseModel, summary="企业微信通知配置状态")
async def wecom_status():
    """查看企业微信通知配置状态（通过 config_manager 三级获取）"""
    from app.config_manager import config_manager

    notify_config = await config_manager.get_group("notify_wecom")
    oauth_config = await config_manager.get_group("oauth_wecom")

    webhook_url = notify_config.get("webhook_url") or ""
    corp_id = oauth_config.get("corp_id") or ""
    agent_id = oauth_config.get("agent_id") or ""
    app_secret = oauth_config.get("app_secret") or ""

    return ResponseModel(
        message="企业微信通知配置状态",
        data={
            "webhook": {
                "configured": bool(webhook_url),
                "url": (webhook_url[:30] + "***") if webhook_url else "",
            },
            "app_message": {
                "configured": bool(corp_id and app_secret and agent_id),
                "corp_id": (corp_id[:4] + "***") if corp_id else "",
                "agent_id": agent_id,
            },
        },
    )


@router.post("/wecom/webhook/test", response_model=ResponseModel, summary="测试企业微信 Webhook")
async def wecom_webhook_test(data: WecomWebhookTestInput):
    """发送测试消息到企业微信群机器人"""
    from app.wecom import WecomWebhook

    if not await WecomWebhook.is_configured_async():
        raise HTTPException(status_code=400, detail="企业微信 Webhook 未配置")

    success = await WecomWebhook.send_text(content=f"[测试] {data.content}")
    if not success:
        raise HTTPException(status_code=500, detail="企业微信 Webhook 发送失败")

    return ResponseModel(message="企业微信 Webhook 测试消息发送成功")


@router.post("/wecom/app-message/test", response_model=ResponseModel, summary="测试企业微信应用消息")
async def wecom_app_message_test(data: WecomAppMessageTestInput, db: AsyncSession = Depends(get_db)):
    """发送测试应用消息到指定用户"""
    from app.wecom import WecomAppMessage

    if not await WecomAppMessage.is_configured_async():
        raise HTTPException(status_code=400, detail="企业微信应用消息未配置，需要配置企业微信 OAuth 应用")

    # 查询用户的企业微信 userid
    from core.user.model import User
    from sqlalchemy import select
    stmt = select(User.wecom_userid, User.name).where(User.id == data.user_id)
    result = await db.execute(stmt)
    row = result.first()

    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="该用户未绑定企业微信账号")

    success = await WecomAppMessage.send_text(
        userid_list=[row[0]],
        content=f"[测试] 这是一条发送给 {row[1] or '用户'} 的测试消息",
    )
    if not success:
        raise HTTPException(status_code=500, detail="企业微信应用消息发送失败")

    return ResponseModel(message="企业微信应用消息测试发送成功")


# ============ 微信公众号模板消息 API ============

@router.get("/wechat-mp/status", response_model=ResponseModel, summary="微信公众号通知配置状态")
async def wechat_mp_status():
    """查看微信公众号模板消息配置状态（通过 config_manager 三级获取）"""
    from app.config_manager import config_manager

    oauth_config = await config_manager.get_group("oauth_wechat")
    mp_config = await config_manager.get_group("notify_wechat_mp")

    app_id = oauth_config.get("app_id") or ""
    app_secret = oauth_config.get("app_secret") or ""
    template_id = mp_config.get("template_id") or ""
    mp_url = mp_config.get("url") or ""
    mini_appid = mp_config.get("mini_appid") or ""

    return ResponseModel(
        message="微信公众号通知配置状态",
        data={
            "configured": bool(app_id and app_secret and template_id),
            "app_id": (app_id[:4] + "***") if app_id else "",
            "template_id": (template_id[:8] + "***") if template_id else "",
            "has_url": bool(mp_url),
            "has_miniprogram": bool(mini_appid),
        },
    )


@router.post("/wechat-mp/test", response_model=ResponseModel, summary="测试微信公众号模板消息")
async def wechat_mp_test(data: WechatMPTestInput, db: AsyncSession = Depends(get_db)):
    """发送测试模板消息到指定用户"""
    from app.wechat import WechatMPMessage

    if not await WechatMPMessage.is_configured_async():
        raise HTTPException(status_code=400, detail="微信公众号模板消息未配置，需要配置微信 OAuth 应用及模板 ID")

    # 查询用户的微信 openid
    from core.user.model import User
    from sqlalchemy import select
    stmt = select(User.wechat_openid, User.name).where(User.id == data.user_id)
    result = await db.execute(stmt)
    row = result.first()

    if not row or not row[0]:
        raise HTTPException(status_code=400, detail="该用户未绑定微信账号")

    success = await WechatMPMessage.send_notification(
        openid=row[0],
        title="测试通知",
        content=f"这是一条发送给 {row[1] or '用户'} 的测试模板消息",
        remark="如果您收到此消息，说明微信公众号通知配置正确",
    )
    if not success:
        raise HTTPException(status_code=500, detail="微信模板消息发送失败")

    return ResponseModel(message="微信公众号模板消息测试发送成功")
