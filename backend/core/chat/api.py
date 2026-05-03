from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.base_schema import ResponseModel
from core.chat.schema import (
    CreatePrivateConversationIn,
    CreateGroupConversationIn,
    UpdateConversationIn,
    ConversationOut,
    ConversationListOut,
    ConversationMemberOut,
    AddMembersIn,
    ConversationSettingIn,
    SendMessageIn,
    ChatMessageOut,
    ChatMessageListOut,
    MarkReadIn,
)
from core.chat.service import ConversationService, ChatMessageService

router = APIRouter(prefix="/chat", tags=["聊天"])


# ============ 会话管理 ============

@router.get("/conversations", response_model=ConversationListOut, summary="我的会话列表")
async def get_conversations(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会话列表"""
    user_id = request.state.user_id
    items = await ConversationService.get_user_conversations(db, user_id)
    return ConversationListOut(
        items=[ConversationOut(**item) for item in items],
        total=len(items),
    )


@router.post("/conversations/private", response_model=ConversationOut, summary="创建/获取单聊")
async def create_private_conversation(
    request: Request,
    data: CreatePrivateConversationIn,
    db: AsyncSession = Depends(get_db),
):
    """创建或获取与某用户的单聊会话"""
    user_id = request.state.user_id
    if data.user_id == user_id:
        raise HTTPException(status_code=400, detail="不能与自己创建单聊")

    conv = await ConversationService.get_or_create_private(db, user_id, data.user_id)

    # 获取对方用户信息
    from core.user.model import User
    from sqlalchemy import select
    peer_result = await db.execute(select(User).where(User.id == data.user_id))
    peer = peer_result.scalar_one_or_none()

    member = await ConversationService.get_member(db, conv.id, user_id)

    return ConversationOut(
        id=conv.id,
        type=conv.type,
        name=conv.name,
        avatar=conv.avatar,
        owner_id=conv.owner_id,
        last_message_time=conv.last_message_time,
        last_message_preview=conv.last_message_preview,
        member_count=conv.member_count,
        sys_create_datetime=conv.sys_create_datetime,
        unread_count=member.unread_count if member else 0,
        is_muted=member.is_muted if member else False,
        is_pinned=member.is_pinned if member else False,
        peer_user_id=peer.id if peer else None,
        peer_user_name=(peer.name or peer.username) if peer else None,
        peer_user_avatar=peer.avatar if peer else None,
    )


@router.post("/conversations/group", response_model=ConversationOut, summary="创建群聊")
async def create_group_conversation(
    request: Request,
    data: CreateGroupConversationIn,
    db: AsyncSession = Depends(get_db),
):
    """创建群聊"""
    user_id = request.state.user_id
    if len(data.member_ids) < 1:
        raise HTTPException(status_code=400, detail="群聊至少需要1个其他成员")

    conv = await ConversationService.create_group(
        db, name=data.name, owner_id=user_id,
        member_ids=data.member_ids, avatar=data.avatar,
    )
    return ConversationOut(
        id=conv.id,
        type=conv.type,
        name=conv.name,
        avatar=conv.avatar,
        owner_id=conv.owner_id,
        last_message_time=conv.last_message_time,
        last_message_preview=conv.last_message_preview,
        member_count=conv.member_count,
        sys_create_datetime=conv.sys_create_datetime,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut, summary="会话详情")
async def get_conversation(
    request: Request,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取会话详情"""
    user_id = request.state.user_id
    conv = await ConversationService.get_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if not await ConversationService.is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=403, detail="非会话成员")

    member = await ConversationService.get_member(db, conversation_id, user_id)
    return ConversationOut(
        id=conv.id,
        type=conv.type,
        name=conv.name,
        avatar=conv.avatar,
        owner_id=conv.owner_id,
        last_message_time=conv.last_message_time,
        last_message_preview=conv.last_message_preview,
        member_count=conv.member_count,
        sys_create_datetime=conv.sys_create_datetime,
        unread_count=member.unread_count if member else 0,
        is_muted=member.is_muted if member else False,
        is_pinned=member.is_pinned if member else False,
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationOut, summary="更新群聊信息")
async def update_conversation(
    request: Request,
    conversation_id: str,
    data: UpdateConversationIn,
    db: AsyncSession = Depends(get_db),
):
    """更新群聊名称/头像"""
    user_id = request.state.user_id
    conv = await ConversationService.get_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.type != "group":
        raise HTTPException(status_code=400, detail="只能更新群聊信息")
    if conv.owner_id != user_id:
        # 检查是否是管理员
        member = await ConversationService.get_member(db, conversation_id, user_id)
        if not member or member.role not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail="无权限修改群聊信息")

    updated = await ConversationService.update_conversation(
        db, conversation_id, name=data.name, avatar=data.avatar,
    )
    return ConversationOut(
        id=updated.id,
        type=updated.type,
        name=updated.name,
        avatar=updated.avatar,
        owner_id=updated.owner_id,
        last_message_time=updated.last_message_time,
        last_message_preview=updated.last_message_preview,
        member_count=updated.member_count,
        sys_create_datetime=updated.sys_create_datetime,
    )


@router.delete("/conversations/{conversation_id}", response_model=ResponseModel, summary="解散群聊")
async def delete_conversation(
    request: Request,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """解散群聊（仅群主）"""
    user_id = request.state.user_id
    conv = await ConversationService.get_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.type != "group":
        raise HTTPException(status_code=400, detail="单聊不能解散")
    if conv.owner_id != user_id:
        raise HTTPException(status_code=403, detail="只有群主可以解散群聊")

    await ConversationService.delete_conversation(db, conversation_id)
    return ResponseModel(message="群聊已解散")


# ============ 成员管理 ============

@router.get("/conversations/{conversation_id}/members", summary="获取成员列表")
async def get_members(
    request: Request,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取会话成员列表"""
    user_id = request.state.user_id
    if not await ConversationService.is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=403, detail="非会话成员")

    members = await ConversationService.get_members(db, conversation_id)
    return [ConversationMemberOut(**m) for m in members]


@router.post("/conversations/{conversation_id}/members", response_model=ResponseModel, summary="添加成员")
async def add_members(
    request: Request,
    conversation_id: str,
    data: AddMembersIn,
    db: AsyncSession = Depends(get_db),
):
    """添加群成员"""
    user_id = request.state.user_id
    conv = await ConversationService.get_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.type != "group":
        raise HTTPException(status_code=400, detail="单聊不能添加成员")
    if not await ConversationService.is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=403, detail="非会话成员")

    added = await ConversationService.add_members(db, conversation_id, data.user_ids)
    return ResponseModel(message=f"已添加 {added} 个成员")


@router.delete("/conversations/{conversation_id}/members/{member_user_id}", response_model=ResponseModel, summary="移除成员")
async def remove_member(
    request: Request,
    conversation_id: str,
    member_user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """移除群成员（群主/管理员操作）"""
    user_id = request.state.user_id
    conv = await ConversationService.get_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    if conv.type != "group":
        raise HTTPException(status_code=400, detail="单聊不能移除成员")

    member = await ConversationService.get_member(db, conversation_id, user_id)
    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="无权限移除成员")
    if member_user_id == conv.owner_id:
        raise HTTPException(status_code=400, detail="不能移除群主")

    success = await ConversationService.remove_member(db, conversation_id, member_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="成员不存在")
    return ResponseModel(message="已移除成员")


# ============ 会话设置 ============

@router.put("/conversations/{conversation_id}/pin", response_model=ResponseModel, summary="置顶/取消置顶")
async def toggle_pin(
    request: Request,
    conversation_id: str,
    data: ConversationSettingIn,
    db: AsyncSession = Depends(get_db),
):
    """置顶或取消置顶会话"""
    user_id = request.state.user_id
    success = await ConversationService.update_setting(
        db, conversation_id, user_id, "is_pinned", data.value,
    )
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在或非成员")
    return ResponseModel(message="设置成功")


@router.put("/conversations/{conversation_id}/mute", response_model=ResponseModel, summary="免打扰设置")
async def toggle_mute(
    request: Request,
    conversation_id: str,
    data: ConversationSettingIn,
    db: AsyncSession = Depends(get_db),
):
    """设置或取消免打扰"""
    user_id = request.state.user_id
    success = await ConversationService.update_setting(
        db, conversation_id, user_id, "is_muted", data.value,
    )
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在或非成员")
    return ResponseModel(message="设置成功")


# ============ 在线状态 ============

@router.get("/users/online", summary="获取在线用户列表")
async def get_online_users(
    request: Request,
):
    """获取当前所有在线用户ID列表"""
    from core.websocket.consumers.base import manager
    online_ids = list(manager.get_online_user_ids())
    return {"user_ids": online_ids}


# ============ 消息管理 ============

@router.get("/messages/unread", summary="获取所有未读聊天消息")
async def get_unread_messages(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100, description="最大数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户所有未读聊天消息（跨会话，按时间倒序）"""
    user_id = request.state.user_id
    items = await ChatMessageService.get_unread_messages(db, user_id, limit=limit)
    return {"items": items, "total": len(items)}


@router.get("/conversations/{conversation_id}/messages", summary="获取消息列表")
async def get_messages(
    request: Request,
    conversation_id: str,
    before_id: Optional[str] = Query(default=None, alias="beforeId", description="游标消息ID"),
    limit: int = Query(default=30, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取消息列表（游标分页，向上加载历史）"""
    user_id = request.state.user_id
    if not await ConversationService.is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=403, detail="非会话成员")

    items, has_more = await ChatMessageService.get_messages(
        db, conversation_id, before_id=before_id, limit=limit,
    )
    return ChatMessageListOut(
        items=[ChatMessageOut(**item) for item in items],
        has_more=has_more,
    )


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageOut, summary="发送消息")
async def send_message(
    request: Request,
    conversation_id: str,
    data: SendMessageIn,
    db: AsyncSession = Depends(get_db),
):
    """发送消息（REST备用，主要走WebSocket）"""
    user_id = request.state.user_id
    if not await ConversationService.is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=403, detail="非会话成员")

    if data.msg_type == "text" and not data.content:
        raise HTTPException(status_code=400, detail="文本消息内容不能为空")
    if data.msg_type in ("image", "file", "voice") and not data.file_id:
        raise HTTPException(status_code=400, detail="文件消息需要提供文件ID")

    msg = await ChatMessageService.send_message(
        db,
        conversation_id=conversation_id,
        sender_id=user_id,
        msg_type=data.msg_type,
        content=data.content,
        file_id=data.file_id,
        reply_to_id=data.reply_to_id,
        extra=data.extra,
    )

    # 获取发送者信息
    from core.user.model import User
    from sqlalchemy import select
    sender_result = await db.execute(select(User).where(User.id == user_id))
    sender = sender_result.scalar_one_or_none()

    # 通过WebSocket推送给会话其他成员
    await _push_message_to_members(db, conversation_id, user_id, msg, sender)

    return ChatMessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        msg_type=msg.msg_type,
        content=msg.content,
        file_id=msg.file_id,
        reply_to_id=msg.reply_to_id,
        is_recalled=msg.is_recalled,
        extra=msg.extra,
        sys_create_datetime=msg.sys_create_datetime,
        sender_name=(sender.name or sender.username) if sender else None,
        sender_avatar=sender.avatar if sender else None,
    )


@router.post("/messages/{message_id}/recall", response_model=ResponseModel, summary="撤回消息")
async def recall_message(
    request: Request,
    message_id: str,
    db: AsyncSession = Depends(get_db),
):
    """撤回消息（2分钟内）"""
    user_id = request.state.user_id
    msg = await ChatMessageService.recall_message(db, message_id, user_id)
    if not msg:
        raise HTTPException(status_code=400, detail="无法撤回消息（超时或非本人消息）")

    # 通过WebSocket通知撤回
    member_ids = await ConversationService.get_member_user_ids(db, msg.conversation_id)
    from core.websocket.consumers.base import manager
    for uid in member_ids:
        await manager.send_to_user(uid, {
            "type": "chat.recalled",
            "data": {
                "conversation_id": msg.conversation_id,
                "message_id": message_id,
            },
        })

    return ResponseModel(message="消息已撤回")


@router.post("/conversations/{conversation_id}/read", response_model=ResponseModel, summary="标记已读")
async def mark_read(
    request: Request,
    conversation_id: str,
    data: MarkReadIn,
    db: AsyncSession = Depends(get_db),
):
    """标记已读到某条消息"""
    user_id = request.state.user_id
    success = await ChatMessageService.mark_read(
        db, conversation_id, user_id, data.message_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在或非成员")

    # 通过WebSocket通知已读回执
    member_ids = await ConversationService.get_member_user_ids(db, conversation_id)
    from core.websocket.consumers.base import manager
    for uid in member_ids:
        if uid != user_id:
            await manager.send_to_user(uid, {
                "type": "chat.read_receipt",
                "data": {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "message_id": data.message_id,
                },
            })

    return ResponseModel(message="已标记已读")


# ============ 辅助函数 ============

async def _push_message_to_members(db, conversation_id, sender_id, msg, sender):
    """通过WebSocket推送消息给会话成员"""
    try:
        member_ids = await ConversationService.get_member_user_ids(db, conversation_id)
        from core.websocket.consumers.base import manager
        message_data = {
            "type": "chat.message",
            "data": {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "sender_id": msg.sender_id,
                "msg_type": msg.msg_type,
                "content": msg.content,
                "file_id": msg.file_id,
                "reply_to_id": msg.reply_to_id,
                "is_recalled": msg.is_recalled,
                "extra": msg.extra,
                "sys_create_datetime": msg.sys_create_datetime.isoformat() if msg.sys_create_datetime else None,
                "sender_name": (sender.name or sender.username) if sender else None,
                "sender_avatar": sender.avatar if sender else None,
            },
        }
        for uid in member_ids:
            await manager.send_to_user(uid, message_data)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"推送聊天消息失败: {e}")


# 需要导入 Optional
from typing import Optional
