# -*- coding: utf-8 -*-
"""
聊天 WebSocket 消费者
"""
import json
import logging
from typing import Dict, Any

from fastapi import WebSocket

from core.websocket.consumers.base import TokenAuthWebSocketConsumer, manager

logger = logging.getLogger(__name__)


class ChatConsumer(TokenAuthWebSocketConsumer):
    """聊天WebSocket消费者"""

    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
        self._conversation_ids: set = set()

    async def connect(self):
        """连接并加入用户聊天组"""
        await super().connect()
        if self.is_authenticated and self.user_id:
            # 加入用户聊天组（用于接收所有聊天消息）
            await manager.group_add(
                f"chat_user_{self.user_id}",
                self.websocket,
            )
            # 广播上线事件给相关会话成员
            await self._broadcast_presence("online")

    async def disconnect(self, close_code: int = 1000):
        """断开连接"""
        if self.user_id:
            # 先广播下线事件（在移除连接之前检查是否还有其他连接）
            await manager.group_discard(
                f"chat_user_{self.user_id}",
                self.websocket,
            )
            # 离开所有会话组
            for conv_id in self._conversation_ids:
                await manager.group_discard(
                    f"chat_conv_{conv_id}",
                    self.websocket,
                )
        await super().disconnect(close_code)
        # 断开后检查用户是否还有其他连接，没有则广播离线
        if self.user_id and not manager.is_online(self.user_id):
            await self._broadcast_presence("offline")

    async def _broadcast_presence(self, status: str):
        """广播用户在线状态变更给所有相关会话成员"""
        try:
            from app.database import AsyncSessionLocal
            from core.chat.service import ConversationService

            async with AsyncSessionLocal() as db:
                # 获取该用户参与的所有会话的成员
                related_user_ids = await ConversationService.get_related_user_ids(db, self.user_id)

            presence_data = {
                "type": "chat.presence",
                "data": {
                    "user_id": self.user_id,
                    "status": status,
                },
            }
            for uid in related_user_ids:
                if uid != self.user_id:
                    await manager.send_to_user(uid, presence_data)
        except Exception as e:
            logger.error(f"广播在线状态失败: {e}")

    async def handle_message(self, data: Dict[str, Any]):
        """处理聊天相关消息"""
        message_type = data.get("type", "unknown")
        payload = data.get("data", {})

        if message_type == "chat.send":
            await self._handle_send(payload)
        elif message_type == "chat.typing":
            await self._handle_typing(payload)
        elif message_type == "chat.read":
            await self._handle_read(payload)
        elif message_type == "chat.join":
            await self._handle_join(payload)
        else:
            await self.send_error(f"未知消息类型: {message_type}")

    async def _handle_send(self, payload: Dict[str, Any]):
        """处理发送消息"""
        conversation_id = payload.get("conversation_id")
        msg_type = payload.get("msg_type", "text")
        content = payload.get("content")
        file_id = payload.get("file_id")
        reply_to_id = payload.get("reply_to_id")
        extra = payload.get("extra")

        if not conversation_id:
            await self.send_error("缺少 conversation_id")
            return

        try:
            from app.database import AsyncSessionLocal
            from core.chat.service import ConversationService, ChatMessageService

            async with AsyncSessionLocal() as db:
                # 验证成员身份
                if not await ConversationService.is_member(db, conversation_id, self.user_id):
                    await self.send_error("非会话成员")
                    return

                # 发送消息
                msg = await ChatMessageService.send_message(
                    db,
                    conversation_id=conversation_id,
                    sender_id=self.user_id,
                    msg_type=msg_type,
                    content=content,
                    file_id=file_id,
                    reply_to_id=reply_to_id,
                    extra=extra,
                )

                # 获取发送者信息
                from core.user.model import User
                from sqlalchemy import select
                sender_result = await db.execute(select(User).where(User.id == self.user_id))
                sender = sender_result.scalar_one_or_none()

                # 获取文件信息
                file_info = {}
                if msg.file_id:
                    from core.file_manager.model import FileManager
                    file_result = await db.execute(
                        select(FileManager).where(FileManager.id == msg.file_id)
                    )
                    f = file_result.scalar_one_or_none()
                    if f:
                        file_info = {
                            "file_name": f.name,
                            "file_url": f"/api/core/file_manager/stream/{f.id}",
                            "file_size": f.size,
                            "file_ext": f.file_ext,
                        }

                # 推送给会话所有成员
                member_ids = await ConversationService.get_member_user_ids(db, conversation_id)
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
                        **file_info,
                    },
                }
                for uid in member_ids:
                    await manager.send_to_user(uid, message_data)

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            await self.send_error(f"发送消息失败: {str(e)}")

    async def _handle_typing(self, payload: Dict[str, Any]):
        """处理正在输入状态"""
        conversation_id = payload.get("conversation_id")
        if not conversation_id:
            return

        try:
            from app.database import AsyncSessionLocal
            from core.chat.service import ConversationService
            from core.user.model import User
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                member_ids = await ConversationService.get_member_user_ids(db, conversation_id)
                sender_result = await db.execute(select(User).where(User.id == self.user_id))
                sender = sender_result.scalar_one_or_none()

                typing_data = {
                    "type": "chat.typing",
                    "data": {
                        "conversation_id": conversation_id,
                        "user_id": self.user_id,
                        "user_name": (sender.name or sender.username) if sender else None,
                    },
                }
                for uid in member_ids:
                    if uid != self.user_id:
                        await manager.send_to_user(uid, typing_data)
        except Exception as e:
            logger.error(f"发送typing状态失败: {e}")

    async def _handle_read(self, payload: Dict[str, Any]):
        """处理已读标记"""
        conversation_id = payload.get("conversation_id")
        message_id = payload.get("message_id")
        if not conversation_id or not message_id:
            return

        try:
            from app.database import AsyncSessionLocal
            from core.chat.service import ConversationService, ChatMessageService

            async with AsyncSessionLocal() as db:
                await ChatMessageService.mark_read(db, conversation_id, self.user_id, message_id)

                # 通知其他成员已读回执
                member_ids = await ConversationService.get_member_user_ids(db, conversation_id)
                read_data = {
                    "type": "chat.read_receipt",
                    "data": {
                        "conversation_id": conversation_id,
                        "user_id": self.user_id,
                        "message_id": message_id,
                    },
                }
                for uid in member_ids:
                    if uid != self.user_id:
                        await manager.send_to_user(uid, read_data)
        except Exception as e:
            logger.error(f"标记已读失败: {e}")

    async def _handle_join(self, payload: Dict[str, Any]):
        """加入会话组（用于接收该会话的实时消息）"""
        conversation_id = payload.get("conversation_id")
        if not conversation_id:
            return

        self._conversation_ids.add(conversation_id)
        await manager.group_add(f"chat_conv_{conversation_id}", self.websocket)
        await self.send_message("chat.joined", f"已加入会话 {conversation_id}")
