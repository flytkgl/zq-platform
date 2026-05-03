import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any

from sqlalchemy import select, func, desc, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_model import generate_nanoid
from core.chat.model import Conversation, ConversationMember, ChatMessage

logger = logging.getLogger(__name__)


class ConversationService:
    """会话服务"""

    @staticmethod
    async def get_or_create_private(
        db: AsyncSession,
        user_id: str,
        peer_user_id: str,
    ) -> Conversation:
        """获取或创建单聊会话"""
        # 查找已有的单聊会话
        subq1 = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id == user_id,
            ConversationMember.is_deleted == False,  # noqa: E712
        )
        subq2 = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id == peer_user_id,
            ConversationMember.is_deleted == False,  # noqa: E712
        )
        result = await db.execute(
            select(Conversation).where(
                Conversation.type == "private",
                Conversation.is_deleted == False,  # noqa: E712
                Conversation.id.in_(subq1),
                Conversation.id.in_(subq2),
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

        # 创建新会话
        conv = Conversation(
            id=generate_nanoid(),
            type="private",
            member_count=2,
        )
        db.add(conv)
        await db.flush()

        # 添加两个成员
        for uid in [user_id, peer_user_id]:
            member = ConversationMember(
                id=generate_nanoid(),
                conversation_id=conv.id,
                user_id=uid,
                role="member",
            )
            db.add(member)

        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def create_group(
        db: AsyncSession,
        name: str,
        owner_id: str,
        member_ids: List[str],
        avatar: Optional[str] = None,
    ) -> Conversation:
        """创建群聊"""
        # 确保群主在成员列表中
        all_member_ids = list(set([owner_id] + member_ids))

        conv = Conversation(
            id=generate_nanoid(),
            type="group",
            name=name,
            avatar=avatar,
            owner_id=owner_id,
            member_count=len(all_member_ids),
        )
        db.add(conv)
        await db.flush()

        for uid in all_member_ids:
            member = ConversationMember(
                id=generate_nanoid(),
                conversation_id=conv.id,
                user_id=uid,
                role="owner" if uid == owner_id else "member",
            )
            db.add(member)

        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """获取用户的会话列表（按最后消息时间降序）"""
        # 查询用户参与的会话
        member_subq = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id == user_id,
            ConversationMember.is_deleted == False,  # noqa: E712
        )
        result = await db.execute(
            select(Conversation).where(
                Conversation.id.in_(member_subq),
                Conversation.is_deleted == False,  # noqa: E712
            ).order_by(
                desc(Conversation.last_message_time),
                desc(Conversation.sys_create_datetime),
            )
        )
        conversations = list(result.scalars().all())

        # 获取当前用户的成员信息
        conv_ids = [c.id for c in conversations]
        if not conv_ids:
            return []

        member_result = await db.execute(
            select(ConversationMember).where(
                ConversationMember.conversation_id.in_(conv_ids),
                ConversationMember.user_id == user_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            )
        )
        member_map = {m.conversation_id: m for m in member_result.scalars().all()}

        # 对于单聊，获取对方用户信息
        private_conv_ids = [c.id for c in conversations if c.type == "private"]
        peer_map: Dict[str, Dict] = {}
        if private_conv_ids:
            peer_result = await db.execute(
                select(ConversationMember).where(
                    ConversationMember.conversation_id.in_(private_conv_ids),
                    ConversationMember.user_id != user_id,
                    ConversationMember.is_deleted == False,  # noqa: E712
                )
            )
            peer_members = list(peer_result.scalars().all())
            # 批量获取用户信息
            peer_user_ids = [pm.user_id for pm in peer_members]
            if peer_user_ids:
                from core.user.model import User
                user_result = await db.execute(
                    select(User).where(User.id.in_(peer_user_ids))
                )
                user_map = {u.id: u for u in user_result.scalars().all()}
                for pm in peer_members:
                    u = user_map.get(pm.user_id)
                    if u:
                        peer_map[pm.conversation_id] = {
                            "peer_user_id": u.id,
                            "peer_user_name": u.name or u.username,
                            "peer_user_avatar": u.avatar,
                        }

        # 组装结果
        items = []
        for conv in conversations:
            member = member_map.get(conv.id)
            item = {
                "id": conv.id,
                "type": conv.type,
                "name": conv.name,
                "avatar": conv.avatar,
                "owner_id": conv.owner_id,
                "last_message_time": conv.last_message_time,
                "last_message_preview": conv.last_message_preview,
                "member_count": conv.member_count,
                "sys_create_datetime": conv.sys_create_datetime,
                "unread_count": member.unread_count if member else 0,
                "is_muted": member.is_muted if member else False,
                "is_pinned": member.is_pinned if member else False,
                "peer_user_id": None,
                "peer_user_name": None,
                "peer_user_avatar": None,
            }
            if conv.type == "private" and conv.id in peer_map:
                item.update(peer_map[conv.id])
            items.append(item)

        # 置顶排序：置顶的在前
        items.sort(key=lambda x: (not x["is_pinned"], 0))
        return items

    @staticmethod
    async def get_by_id(db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        """获取会话"""
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def is_member(db: AsyncSession, conversation_id: str, user_id: str) -> bool:
        """检查用户是否是会话成员"""
        result = await db.execute(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_member(
        db: AsyncSession, conversation_id: str, user_id: str
    ) -> Optional[ConversationMember]:
        """获取成员记录"""
        result = await db.execute(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_members(
        db: AsyncSession, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """获取会话成员列表（含用户信息）"""
        result = await db.execute(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            ).order_by(ConversationMember.joined_at)
        )
        members = list(result.scalars().all())

        # 批量获取用户信息
        user_ids = [m.user_id for m in members]
        if not user_ids:
            return []

        from core.user.model import User
        user_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        user_map = {u.id: u for u in user_result.scalars().all()}

        items = []
        for m in members:
            u = user_map.get(m.user_id)
            items.append({
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "nickname": m.nickname,
                "is_muted": m.is_muted,
                "is_pinned": m.is_pinned,
                "unread_count": m.unread_count,
                "joined_at": m.joined_at,
                "user_name": (u.name or u.username) if u else None,
                "user_avatar": u.avatar if u else None,
            })
        return items

    @staticmethod
    async def add_members(
        db: AsyncSession,
        conversation_id: str,
        user_ids: List[str],
    ) -> int:
        """添加群成员，返回实际添加数量"""
        added = 0
        for uid in user_ids:
            # 检查是否已是成员
            existing = await db.execute(
                select(ConversationMember).where(
                    ConversationMember.conversation_id == conversation_id,
                    ConversationMember.user_id == uid,
                )
            )
            member = existing.scalar_one_or_none()
            if member:
                if member.is_deleted:
                    member.is_deleted = False
                    added += 1
                continue

            new_member = ConversationMember(
                id=generate_nanoid(),
                conversation_id=conversation_id,
                user_id=uid,
                role="member",
            )
            db.add(new_member)
            added += 1

        if added > 0:
            # 更新成员数
            conv = await ConversationService.get_by_id(db, conversation_id)
            if conv:
                conv.member_count = (conv.member_count or 0) + added
            await db.commit()
        return added

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        """移除群成员"""
        member = await ConversationService.get_member(db, conversation_id, user_id)
        if not member:
            return False

        member.is_deleted = True
        conv = await ConversationService.get_by_id(db, conversation_id)
        if conv:
            conv.member_count = max(0, (conv.member_count or 0) - 1)
        await db.commit()
        return True

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: str,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> Optional[Conversation]:
        """更新群聊信息"""
        conv = await ConversationService.get_by_id(db, conversation_id)
        if not conv:
            return None
        if name is not None:
            conv.name = name
        if avatar is not None:
            conv.avatar = avatar
        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def update_setting(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        field: str,
        value: bool,
    ) -> bool:
        """更新会话设置（置顶/免打扰）"""
        member = await ConversationService.get_member(db, conversation_id, user_id)
        if not member:
            return False
        setattr(member, field, value)
        await db.commit()
        return True

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """解散群聊（软删除）"""
        conv = await ConversationService.get_by_id(db, conversation_id)
        if not conv:
            return False
        conv.is_deleted = True
        await db.commit()
        return True

    @staticmethod
    async def get_member_user_ids(
        db: AsyncSession,
        conversation_id: str,
    ) -> List[str]:
        """获取会话所有成员的user_id"""
        result = await db.execute(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def get_related_user_ids(
        db: AsyncSession,
        user_id: str,
    ) -> List[str]:
        """获取与指定用户有共同会话的所有用户ID"""
        # 先获取该用户参与的所有会话ID
        conv_ids_result = await db.execute(
            select(ConversationMember.conversation_id).where(
                ConversationMember.user_id == user_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            )
        )
        conv_ids = [row[0] for row in conv_ids_result.all()]
        if not conv_ids:
            return []

        # 获取这些会话中的所有成员user_id
        result = await db.execute(
            select(ConversationMember.user_id).where(
                ConversationMember.conversation_id.in_(conv_ids),
                ConversationMember.is_deleted == False,  # noqa: E712
            ).distinct()
        )
        return [row[0] for row in result.all()]


class ChatMessageService:
    """聊天消息服务"""

    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: str,
        sender_id: str,
        msg_type: str = "text",
        content: Optional[str] = None,
        file_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """发送消息"""
        msg = ChatMessage(
            id=generate_nanoid(),
            conversation_id=conversation_id,
            sender_id=sender_id,
            msg_type=msg_type,
            content=content,
            file_id=file_id,
            reply_to_id=reply_to_id,
            extra=extra,
        )
        db.add(msg)
        await db.flush()

        # 更新会话最后消息
        preview = content[:200] if content else f"[{msg_type}]"
        await db.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(
                last_message_id=msg.id,
                last_message_time=msg.sys_create_datetime,
                last_message_preview=preview,
            )
        )

        # 更新其他成员的未读数
        await db.execute(
            update(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id != sender_id,
                ConversationMember.is_deleted == False,  # noqa: E712
            ).values(
                unread_count=ConversationMember.unread_count + 1,
            )
        )

        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: str,
        before_id: Optional[str] = None,
        limit: int = 30,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """获取消息列表（游标分页，向上加载历史）"""
        query = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.is_deleted == False,  # noqa: E712
        )

        if before_id:
            # 获取游标消息的创建时间
            cursor_result = await db.execute(
                select(ChatMessage.sys_create_datetime).where(ChatMessage.id == before_id)
            )
            cursor_time = cursor_result.scalar_one_or_none()
            if cursor_time:
                query = query.where(ChatMessage.sys_create_datetime < cursor_time)

        # 多取一条判断是否有更多
        result = await db.execute(
            query.order_by(desc(ChatMessage.sys_create_datetime)).limit(limit + 1)
        )
        messages = list(result.scalars().all())
        has_more = len(messages) > limit
        messages = messages[:limit]

        # 批量获取发送者信息
        sender_ids = list(set(m.sender_id for m in messages))
        sender_map: Dict[str, Any] = {}
        if sender_ids:
            from core.user.model import User
            user_result = await db.execute(
                select(User).where(User.id.in_(sender_ids))
            )
            sender_map = {u.id: u for u in user_result.scalars().all()}

        # 获取回复消息预览
        reply_ids = [m.reply_to_id for m in messages if m.reply_to_id]
        reply_map: Dict[str, Dict] = {}
        if reply_ids:
            reply_result = await db.execute(
                select(ChatMessage).where(ChatMessage.id.in_(reply_ids))
            )
            for rm in reply_result.scalars().all():
                sender = sender_map.get(rm.sender_id)
                reply_map[rm.id] = {
                    "reply_to_preview": rm.content[:100] if rm.content else f"[{rm.msg_type}]",
                    "reply_to_sender_name": (sender.name or sender.username) if sender else None,
                }

        # 批量获取文件信息
        file_ids = [m.file_id for m in messages if m.file_id]
        file_map: Dict[str, Any] = {}
        if file_ids:
            from core.file_manager.model import FileManager
            file_result = await db.execute(
                select(FileManager).where(FileManager.id.in_(file_ids))
            )
            for f in file_result.scalars().all():
                file_map[f.id] = {
                    "file_name": f.name,
                    "file_url": f"/api/core/file_manager/stream/{f.id}",
                    "file_size": f.size,
                    "file_ext": f.file_ext,
                }

        # 组装结果
        items = []
        for m in messages:
            sender = sender_map.get(m.sender_id)
            file_info = file_map.get(m.file_id) if m.file_id else None
            item = {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "sender_id": m.sender_id,
                "msg_type": m.msg_type,
                "content": m.content,
                "file_id": m.file_id,
                "reply_to_id": m.reply_to_id,
                "is_recalled": m.is_recalled,
                "recalled_at": m.recalled_at,
                "extra": m.extra,
                "sys_create_datetime": m.sys_create_datetime,
                "sender_name": (sender.name or sender.username) if sender else None,
                "sender_avatar": sender.avatar if sender else None,
                "reply_to_preview": None,
                "reply_to_sender_name": None,
                "file_name": file_info["file_name"] if file_info else None,
                "file_url": file_info["file_url"] if file_info else None,
                "file_size": file_info["file_size"] if file_info else None,
                "file_ext": file_info["file_ext"] if file_info else None,
            }
            if m.reply_to_id and m.reply_to_id in reply_map:
                item.update(reply_map[m.reply_to_id])
            items.append(item)

        # 按时间正序返回（前端从上到下显示）
        items.reverse()
        return items, has_more

    @staticmethod
    async def recall_message(
        db: AsyncSession,
        message_id: str,
        user_id: str,
        recall_timeout_minutes: int = 2,
    ) -> Optional[ChatMessage]:
        """撤回消息（限制时间内）"""
        result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.id == message_id,
                ChatMessage.sender_id == user_id,
                ChatMessage.is_deleted == False,  # noqa: E712
                ChatMessage.is_recalled == False,  # noqa: E712
            )
        )
        msg = result.scalar_one_or_none()
        if not msg:
            return None

        # 检查时间限制
        if msg.sys_create_datetime:
            elapsed = datetime.utcnow() - msg.sys_create_datetime
            if elapsed > timedelta(minutes=recall_timeout_minutes):
                return None

        msg.is_recalled = True
        msg.recalled_at = datetime.utcnow()
        msg.content = None

        # 更新会话最后消息预览
        conv = await db.execute(
            select(Conversation).where(Conversation.last_message_id == message_id)
        )
        conversation = conv.scalar_one_or_none()
        if conversation:
            conversation.last_message_preview = "[消息已撤回]"

        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        message_id: str,
    ) -> bool:
        """标记已读到某条消息"""
        member = await ConversationService.get_member(db, conversation_id, user_id)
        if not member:
            return False

        member.last_read_message_id = message_id
        member.unread_count = 0
        await db.commit()
        return True

    @staticmethod
    async def get_unread_messages(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取用户所有未读聊天消息（跨会话）"""
        from core.user.model import User

        # 查询用户所在的有未读消息的会话
        member_result = await db.execute(
            select(ConversationMember).where(
                ConversationMember.user_id == user_id,
                ConversationMember.is_deleted == False,  # noqa: E712
                ConversationMember.unread_count > 0,
            )
        )
        members = list(member_result.scalars().all())
        if not members:
            return []

        # 收集所有未读消息
        all_messages: List[Dict[str, Any]] = []
        for member in members:
            conv_id = member.conversation_id
            last_read_id = member.last_read_message_id

            # 构建查询：获取 last_read_message_id 之后的消息（非自己发的）
            query = select(ChatMessage).where(
                ChatMessage.conversation_id == conv_id,
                ChatMessage.is_deleted == False,  # noqa: E712
                ChatMessage.is_recalled == False,  # noqa: E712
                ChatMessage.sender_id != user_id,
            )

            if last_read_id:
                # 获取最后已读消息的时间
                cursor_result = await db.execute(
                    select(ChatMessage.sys_create_datetime).where(ChatMessage.id == last_read_id)
                )
                cursor_time = cursor_result.scalar_one_or_none()
                if cursor_time:
                    query = query.where(ChatMessage.sys_create_datetime > cursor_time)

            result = await db.execute(
                query.order_by(desc(ChatMessage.sys_create_datetime)).limit(limit)
            )
            messages = list(result.scalars().all())

            for m in messages:
                all_messages.append({
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "sender_id": m.sender_id,
                    "msg_type": m.msg_type,
                    "content": m.content,
                    "file_id": m.file_id,
                    "is_recalled": m.is_recalled,
                    "sys_create_datetime": m.sys_create_datetime,
                    "sender_name": None,
                    "sender_avatar": None,
                    "conversation_name": None,
                })

        # 批量获取发送者信息
        sender_ids = list(set(m["sender_id"] for m in all_messages))
        sender_map: Dict[str, Any] = {}
        if sender_ids:
            user_result = await db.execute(
                select(User).where(User.id.in_(sender_ids))
            )
            sender_map = {u.id: u for u in user_result.scalars().all()}

        # 批量获取会话信息
        conv_ids = list(set(m["conversation_id"] for m in all_messages))
        conv_map: Dict[str, Any] = {}
        if conv_ids:
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id.in_(conv_ids))
            )
            conv_map = {c.id: c for c in conv_result.scalars().all()}

        # 填充发送者和会话信息
        for m in all_messages:
            sender = sender_map.get(m["sender_id"])
            if sender:
                m["sender_name"] = sender.name or sender.username
                m["sender_avatar"] = sender.avatar
            conv = conv_map.get(m["conversation_id"])
            if conv:
                m["conversation_name"] = conv.name

        # 按时间倒序排列，取最新的 limit 条
        all_messages.sort(key=lambda x: x.get("sys_create_datetime") or "", reverse=True)
        return all_messages[:limit]

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: str) -> Optional[ChatMessage]:
        """获取消息"""
        result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.id == message_id,
                ChatMessage.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def send_system_notification(
        db: AsyncSession,
        recipient_id: str,
        content: str,
        title: str = "",
        link_type: str = "",
        link_id: str = "",
    ) -> Optional[ChatMessage]:
        """
        以系统通知用户身份发送聊天消息

        自动获取/创建系统通知用户，创建单聊会话，发送消息并通过 WebSocket 推送。
        extra 中携带 notify=True, title, link_type, link_id 供前端渲染通知卡片。
        """
        from core.user.model import User

        # 获取系统通知用户
        system_user_id = await ChatMessageService._get_system_notify_user_id(db)
        if not system_user_id:
            logger.warning("系统通知用户未配置且自动创建失败，跳过聊天通知")
            return None

        # 获取或创建单聊会话
        conv = await ConversationService.get_or_create_private(db, system_user_id, recipient_id)

        # 构建 extra 数据（前端根据 notify=True 渲染为通知卡片）
        extra = {"notify": True}
        if title:
            extra["title"] = title
        if link_type:
            extra["link_type"] = link_type
        if link_id:
            extra["link_id"] = link_id

        # 发送消息
        msg = await ChatMessageService.send_message(
            db,
            conversation_id=conv.id,
            sender_id=system_user_id,
            msg_type="text",
            content=content,
            extra=extra,
        )

        # WebSocket 推送
        try:
            from core.websocket.consumers.base import manager

            sender_result = await db.execute(select(User).where(User.id == system_user_id))
            sender = sender_result.scalar_one_or_none()

            message_data = {
                "type": "chat.message",
                "data": {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "sender_id": msg.sender_id,
                    "msg_type": msg.msg_type,
                    "content": msg.content,
                    "file_id": None,
                    "reply_to_id": None,
                    "is_recalled": False,
                    "extra": msg.extra,
                    "sys_create_datetime": msg.sys_create_datetime.isoformat() if msg.sys_create_datetime else None,
                    "sender_name": (sender.name or sender.username) if sender else "系统通知",
                    "sender_avatar": sender.avatar if sender else None,
                },
            }
            await manager.send_to_user(recipient_id, message_data)
        except Exception as e:
            logger.error(f"聊天通知 WebSocket 推送失败: {e}")

        return msg

    @staticmethod
    async def _get_system_notify_user_id(db: AsyncSession) -> Optional[str]:
        """获取系统通知用户 ID，如未配置则自动创建"""
        from app.config import settings
        from core.user.model import User

        # 优先使用配置的 ID
        if settings.SYSTEM_NOTIFY_USER_ID:
            result = await db.execute(
                select(User.id).where(
                    User.id == settings.SYSTEM_NOTIFY_USER_ID,
                    User.is_deleted == False,  # noqa: E712
                )
            )
            if result.scalar_one_or_none():
                return settings.SYSTEM_NOTIFY_USER_ID

        # 查找已有的系统通知用户（username='system_notify'）
        result = await db.execute(
            select(User).where(
                User.username == "system_notify",
                User.is_deleted == False,  # noqa: E712
            )
        )
        user = result.scalar_one_or_none()
        if user:
            return user.id

        # 自动创建
        try:
            user = User(
                id=generate_nanoid(),
                username="system_notify",
                name="系统通知",
                user_type=0,
                user_status=1,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"自动创建系统通知用户: {user.id}")
            return user.id
        except Exception as e:
            logger.error(f"创建系统通知用户失败: {e}")
            await db.rollback()
            return None
