#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消息中心服务（异步版本）
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_compat import json_contains
from core.message.model import Message, Announcement, AnnouncementRead

logger = logging.getLogger(__name__)


class MessageService:
    """消息管理服务"""

    @staticmethod
    async def get_list(
            db: AsyncSession,
            user_id: str,
            msg_type: str = None,
            status: str = None,
            page: int = 1,
            page_size: int = 20,
    ) -> Tuple[List[Message], int]:
        """获取用户消息列表（排除公告类型，公告有独立管理体系）"""
        conditions = [
            Message.recipient_id == user_id,
            Message.is_deleted == False,
            Message.msg_type != "announcement",
        ]

        if msg_type:
            conditions.append(Message.msg_type == msg_type)
        if status:
            conditions.append(Message.status == status)

        # 获取总数
        count_stmt = select(func.count(Message.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表
        offset = (page - 1) * page_size
        stmt = select(Message).where(and_(*conditions)).order_by(
            Message.sys_create_datetime.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: str) -> int:
        """获取未读消息数量（排除公告类型）"""
        stmt = select(func.count(Message.id)).where(
            Message.recipient_id == user_id,
            Message.status == "unread",
            Message.is_deleted == False,
            Message.msg_type != "announcement",
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    async def get_unread_count_by_type(db: AsyncSession, user_id: str) -> Dict[str, int]:
        """按类型获取未读消息数量（排除公告类型）"""
        stmt = select(Message.msg_type, func.count(Message.id)).where(
            Message.recipient_id == user_id,
            Message.status == "unread",
            Message.is_deleted == False,
            Message.msg_type != "announcement",
        ).group_by(Message.msg_type)

        result = await db.execute(stmt)
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: str, user_id: str) -> Optional[Message]:
        """获取消息详情"""
        stmt = select(Message).where(
            Message.id == message_id,
            Message.recipient_id == user_id,
            Message.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_as_read(db: AsyncSession, message_id: str, user_id: str) -> bool:
        """标记消息为已读"""
        message = await MessageService.get_by_id(db, message_id, user_id)
        if not message:
            return False

        if message.status == "unread":
            message.status = "read"
            message.read_at = datetime.now()
            await db.commit()

        return True

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: str, msg_type: str = None) -> int:
        """标记所有消息为已读（排除公告类型）"""
        conditions = [
            Message.recipient_id == user_id,
            Message.status == "unread",
            Message.is_deleted == False,
            Message.msg_type != "announcement",
        ]

        if msg_type:
            conditions.append(Message.msg_type == msg_type)

        stmt = update(Message).where(and_(*conditions)).values(
            status="read",
            read_at=datetime.now(),
        )

        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount

    @staticmethod
    async def delete(db: AsyncSession, message_id: str, user_id: str) -> bool:
        """删除消息（软删除）"""
        message = await MessageService.get_by_id(db, message_id, user_id)
        if not message:
            return False

        message.is_deleted = True
        await db.commit()

        return True

    @staticmethod
    async def delete_all_read(db: AsyncSession, user_id: str) -> int:
        """删除所有已读消息（排除公告类型）"""
        stmt = update(Message).where(
            Message.recipient_id == user_id,
            Message.status == "read",
            Message.is_deleted == False,
            Message.msg_type != "announcement",
        ).values(is_deleted=True)

        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount

    @staticmethod
    async def create_message(
            db: AsyncSession,
            recipient_id: str,
            title: str,
            content: str,
            msg_type: str = "system",
            link_type: str = "",
            link_id: str = "",
            sender_id: str = None,
    ) -> Message:
        """创建消息"""
        message = Message(
            recipient_id=recipient_id,
            title=title,
            content=content,
            msg_type=msg_type,
            link_type=link_type,
            link_id=link_id,
            sender_id=sender_id,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        # WebSocket 实时推送
        await MessageService._push_ws_notification(message)

        return message

    @staticmethod
    async def batch_create_messages(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
            msg_type: str = "system",
            link_type: str = "",
            link_id: str = "",
            sender_id: str = None,
    ) -> List[Message]:
        """批量创建消息"""
        messages = []
        for recipient_id in recipient_ids:
            message = Message(
                recipient_id=recipient_id,
                title=title,
                content=content,
                msg_type=msg_type,
                link_type=link_type,
                link_id=link_id,
                sender_id=sender_id,
            )
            messages.append(message)

        db.add_all(messages)
        await db.commit()

        # WebSocket 实时推送（并发）
        if messages:
            await asyncio.gather(
                *(MessageService._push_ws_notification(msg) for msg in messages),
                return_exceptions=True,
            )

        return messages

    @staticmethod
    async def _push_ws_notification(message: Message) -> None:
        """通过 WebSocket 推送消息通知给接收人（仅推送到通知组）"""
        try:
            from core.websocket.consumers.base import manager

            notification_data = {
                "type": "notification",
                "message": "新消息",
                "data": {
                    "id": str(message.id),
                    "title": message.title,
                    "content": message.content[:100] if message.content else "",
                    "msg_type": message.msg_type,
                    "link_type": message.link_type or "",
                    "link_id": message.link_id or "",
                    "sender_id": str(message.sender_id) if message.sender_id else None,
                },
            }
            # 通过用户专属通知组广播，避免向监控等其他连接发送无关消息
            await manager.broadcast_to_group(
                f"notifications_user_{message.recipient_id}",
                notification_data
            )
        except Exception as e:
            logger.warning(f"WebSocket推送失败: {e}")


class AnnouncementService:
    """公告管理服务"""

    @staticmethod
    async def get_list(
            db: AsyncSession,
            page: int = 1,
            page_size: int = 20,
            status: str = None,
            keyword: str = None,
    ) -> Tuple[List[Announcement], int]:
        """获取公告列表（管理端）"""
        conditions = [Announcement.is_deleted == False]

        if status:
            conditions.append(Announcement.status == status)
        if keyword:
            conditions.append(
                or_(
                    Announcement.title.ilike(f"%{keyword}%"),
                    Announcement.content.ilike(f"%{keyword}%"),
                )
            )

        # 获取总数
        count_stmt = select(func.count(Announcement.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表
        offset = (page - 1) * page_size
        stmt = select(Announcement).where(and_(*conditions)).order_by(
            Announcement.is_top.desc(),
            Announcement.priority.desc(),
            Announcement.publish_time.desc(),
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def get_user_announcements(
            db: AsyncSession,
            user_id: str,
            user_dept_ids: List[str] = None,
            user_role_ids: List[str] = None,
            page: int = 1,
            page_size: int = 20,
            unread_only: bool = False,
    ) -> Tuple[List[Announcement], int]:
        """获取用户可见的公告列表"""
        now = datetime.now()

        # 基础查询：已发布且未过期
        conditions = [
            Announcement.status == "published",
            Announcement.is_deleted == False,
            or_(Announcement.expire_time.is_(None), Announcement.expire_time > now),
        ]

        # 过滤接收范围 - 使用跨数据库兼容的 json_contains
        target_conditions = [Announcement.target_type == "all"]

        if user_dept_ids:
            for dept_id in user_dept_ids:
                target_conditions.append(
                    and_(
                        Announcement.target_type == "dept",
                        json_contains(Announcement.target_ids, dept_id)
                    )
                )

        if user_role_ids:
            for role_id in user_role_ids:
                target_conditions.append(
                    and_(
                        Announcement.target_type == "role",
                        json_contains(Announcement.target_ids, role_id)
                    )
                )

        target_conditions.append(
            and_(
                Announcement.target_type == "user",
                json_contains(Announcement.target_ids, user_id)
            )
        )

        conditions.append(or_(*target_conditions))

        # 只看未读
        if unread_only:
            read_stmt = select(AnnouncementRead.announcement_id).where(
                AnnouncementRead.user_id == user_id
            )
            read_result = await db.execute(read_stmt)
            read_ids = [row[0] for row in read_result.all()]
            if read_ids:
                conditions.append(Announcement.id.notin_(read_ids))

        # 获取总数
        count_stmt = select(func.count(Announcement.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表
        offset = (page - 1) * page_size
        stmt = select(Announcement).where(and_(*conditions)).order_by(
            Announcement.is_top.desc(),
            Announcement.priority.desc(),
            Announcement.publish_time.desc(),
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        # 标记已读状态
        if items:
            read_stmt = select(AnnouncementRead.announcement_id).where(
                AnnouncementRead.user_id == user_id,
                AnnouncementRead.announcement_id.in_([a.id for a in items])
            )
            read_result = await db.execute(read_stmt)
            read_ids = set(row[0] for row in read_result.all())

            for item in items:
                item.is_read = item.id in read_ids

        return items, total

    @staticmethod
    async def get_by_id(db: AsyncSession, announcement_id: str) -> Optional[Announcement]:
        """获取公告详情"""
        stmt = select(Announcement).where(
            Announcement.id == announcement_id,
            Announcement.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
            db: AsyncSession,
            data: Dict[str, Any],
            user_id: str,
    ) -> Announcement:
        """创建公告"""
        announcement = Announcement(
            title=data["title"],
            content=data["content"],
            summary=data.get("summary", ""),
            status=data.get("status", "draft"),
            priority=data.get("priority", 0),
            is_top=data.get("is_top", False),
            target_type=data.get("target_type", "all"),
            target_ids=data.get("target_ids", []),
            publish_time=data.get("publish_time"),
            expire_time=data.get("expire_time"),
            publisher_id=user_id,
            sys_creator_id=user_id,
            sys_modifier_id=user_id,
        )
        db.add(announcement)
        await db.commit()
        await db.refresh(announcement)

        return announcement

    @staticmethod
    async def update(
            db: AsyncSession,
            announcement_id: str,
            data: Dict[str, Any],
            user_id: str,
    ) -> Optional[Announcement]:
        """更新公告"""
        announcement = await AnnouncementService.get_by_id(db, announcement_id)
        if not announcement:
            return None

        # 更新字段
        for field in ["title", "content", "summary", "status", "priority",
                      "is_top", "target_type", "target_ids", "publish_time", "expire_time"]:
            if field in data and data[field] is not None:
                setattr(announcement, field, data[field])

        announcement.sys_modifier_id = user_id
        await db.commit()
        await db.refresh(announcement)

        return announcement

    @staticmethod
    async def delete(db: AsyncSession, announcement_id: str, user_id: str) -> bool:
        """删除公告（软删除）"""
        announcement = await AnnouncementService.get_by_id(db, announcement_id)
        if not announcement:
            return False

        announcement.is_deleted = True
        announcement.sys_modifier_id = user_id
        await db.commit()

        return True

    @staticmethod
    async def publish(
            db: AsyncSession,
            announcement_id: str,
            user_id: str,
    ) -> Optional[Announcement]:
        """发布公告"""
        announcement = await AnnouncementService.get_by_id(db, announcement_id)
        if not announcement:
            return None

        if announcement.status != "draft":
            raise ValueError("只能发布草稿状态的公告")

        announcement.status = "published"
        announcement.publish_time = datetime.now()
        announcement.publisher_id = user_id
        announcement.sys_modifier_id = user_id
        await db.commit()
        await db.refresh(announcement)

        # WebSocket 实时推送公告通知给所有在线用户
        await AnnouncementService._push_announcement_notification(announcement)

        return announcement

    @staticmethod
    async def _push_announcement_notification(announcement: Announcement) -> None:
        """通过 WebSocket 推送公告通知给所有在线用户"""
        try:
            from core.websocket.consumers.base import manager

            notification_data = {
                "type": "announcement",
                "message": "新公告",
                "data": {
                    "id": str(announcement.id),
                    "title": announcement.title,
                    "summary": announcement.summary or "",
                    "priority": announcement.priority,
                    "is_top": announcement.is_top,
                },
            }
            # 向所有在线用户的通知组广播
            for group_name in list(manager.groups.keys()):
                if group_name.startswith("notifications_user_"):
                    await manager.broadcast_to_group(group_name, notification_data)
        except Exception as e:
            logger.warning(f"WebSocket推送公告失败: {e}")

    @staticmethod
    async def mark_as_read(
            db: AsyncSession,
            announcement_id: str,
            user_id: str,
    ) -> bool:
        """标记公告为已读"""
        announcement = await AnnouncementService.get_by_id(db, announcement_id)
        if not announcement:
            return False

        # 检查是否已读
        stmt = select(AnnouncementRead).where(
            AnnouncementRead.announcement_id == announcement_id,
            AnnouncementRead.user_id == user_id,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            # 创建阅读记录
            read_record = AnnouncementRead(
                announcement_id=announcement_id,
                user_id=user_id,
                read_at=datetime.now(),
                sys_creator_id=user_id,
                sys_modifier_id=user_id,
            )
            db.add(read_record)

            # 更新阅读计数
            announcement.read_count = (announcement.read_count or 0) + 1

            await db.commit()

        return True

    @staticmethod
    async def get_unread_count(
            db: AsyncSession,
            user_id: str,
            user_dept_ids: List[str] = None,
            user_role_ids: List[str] = None,
    ) -> int:
        """获取未读公告数量"""
        now = datetime.now()

        # 基础查询
        conditions = [
            Announcement.status == "published",
            Announcement.is_deleted == False,
            or_(Announcement.expire_time.is_(None), Announcement.expire_time > now),
        ]

        # 过滤接收范围 - 使用跨数据库兼容的 json_contains
        target_conditions = [Announcement.target_type == "all"]

        if user_dept_ids:
            for dept_id in user_dept_ids:
                target_conditions.append(
                    and_(
                        Announcement.target_type == "dept",
                        json_contains(Announcement.target_ids, dept_id)
                    )
                )

        if user_role_ids:
            for role_id in user_role_ids:
                target_conditions.append(
                    and_(
                        Announcement.target_type == "role",
                        json_contains(Announcement.target_ids, role_id)
                    )
                )

        target_conditions.append(
            and_(
                Announcement.target_type == "user",
                json_contains(Announcement.target_ids, user_id)
            )
        )

        conditions.append(or_(*target_conditions))

        # 排除已读
        read_stmt = select(AnnouncementRead.announcement_id).where(
            AnnouncementRead.user_id == user_id
        )
        read_result = await db.execute(read_stmt)
        read_ids = [row[0] for row in read_result.all()]
        if read_ids:
            conditions.append(Announcement.id.notin_(read_ids))

        # 获取数量
        count_stmt = select(func.count(Announcement.id)).where(and_(*conditions))
        result = await db.execute(count_stmt)
        return result.scalar() or 0

    @staticmethod
    async def get_read_stats(db: AsyncSession, announcement_id: str) -> Optional[Dict[str, Any]]:
        """获取公告阅读统计"""
        announcement = await AnnouncementService.get_by_id(db, announcement_id)
        if not announcement:
            return None

        # 获取阅读记录
        stmt = select(AnnouncementRead).where(
            AnnouncementRead.announcement_id == announcement_id
        ).order_by(AnnouncementRead.read_at.desc()).limit(100)

        result = await db.execute(stmt)
        reads = result.scalars().all()

        # 获取用户信息
        from core.user.model import User
        user_ids = [r.user_id for r in reads]
        if user_ids:
            user_stmt = select(User).where(User.id.in_(user_ids))
            user_result = await db.execute(user_stmt)
            users = {u.id: u for u in user_result.scalars().all()}
        else:
            users = {}

        return {
            "total_read": len(reads),
            "readers": [
                {
                    "user_id": r.user_id,
                    "user_name": users.get(r.user_id).name if users.get(r.user_id) else "",
                    "read_at": r.read_at.isoformat() if r.read_at else None,
                }
                for r in reads
            ]
        }


class NotifyService:
    """通知服务"""

    @staticmethod
    def parse_template(template: str, context: Dict[str, Any]) -> str:
        """解析模板变量"""
        if not template or not context:
            return template

        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split(".")
            value = context

            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, "")
                else:
                    value = ""
                    break

            return str(value) if value else ""

        return re.sub(r"\$\{([^}]+)\}", replace_var, template)

    @staticmethod
    async def send(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
            channels: List[str] = None,
            msg_type: str = "system",
            context: Dict[str, Any] = None,
            link_type: str = "",
            link_id: str = "",
            sender_id: str = None,
    ) -> Dict[str, bool]:
        """发送通知"""
        if channels is None:
            channels = ["site"]

        # 解析模板变量
        if context:
            title = NotifyService.parse_template(title, context)
            content = NotifyService.parse_template(content, context)

        results = {}

        for channel in channels:
            try:
                if channel == "site":
                    await MessageService.batch_create_messages(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                        msg_type=msg_type,
                        link_type=link_type,
                        link_id=link_id,
                        sender_id=sender_id,
                    )
                    results["site"] = True
                    logger.info(f"站内消息发送成功: {len(recipient_ids)} 条")
                elif channel == "email":
                    results["email"] = await NotifyService._send_email(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                    )
                elif channel == "dingtalk":
                    results["dingtalk"] = await NotifyService._send_dingtalk(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                    )
                elif channel == "feishu":
                    results["feishu"] = await NotifyService._send_feishu(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                    )
                elif channel == "wechat":
                    results["wechat"] = await NotifyService._send_wecom(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                    )
                elif channel == "wechat_mp":
                    results["wechat_mp"] = await NotifyService._send_wechat_mp(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                    )
                elif channel == "sms":
                    results["sms"] = await NotifyService._send_sms(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                    )
                elif channel == "chat":
                    results["chat"] = await NotifyService._send_chat(
                        db=db,
                        recipient_ids=recipient_ids,
                        title=title,
                        content=content,
                        link_type=link_type,
                        link_id=link_id,
                    )
                else:
                    logger.warning(f"未实现的通知渠道: {channel}")
                    results[channel] = False
            except Exception as e:
                logger.error(f"发送通知失败 [{channel}]: {e}")
                results[channel] = False

        return results

    @staticmethod
    async def _send_email(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
    ) -> bool:
        """通过邮件渠道发送通知"""
        from app.email import EmailSender

        if not await EmailSender.is_configured_async():
            logger.warning("SMTP 未配置，跳过邮件发送")
            return False

        # 查询收件人邮箱
        from core.user.model import User
        stmt = select(User.id, User.email).where(
            User.id.in_(recipient_ids),
            User.email.isnot(None),
            User.email != "",
        )
        result = await db.execute(stmt)
        user_emails = {str(row[0]): row[1] for row in result.all()}

        if not user_emails:
            logger.info("没有收件人配置了邮箱，跳过邮件发送")
            return True

        # 构建 HTML 邮件
        html_content = EmailSender.build_notification_html(title, content)

        # 批量发送
        email_list = list(user_emails.values())
        send_results = await EmailSender.send_batch(email_list, title, html_content, html=True)

        success_count = sum(1 for v in send_results.values() if v)
        fail_count = len(send_results) - success_count
        logger.info(f"邮件发送完成: 成功 {success_count}, 失败 {fail_count}")

        return fail_count == 0

    @staticmethod
    async def _send_dingtalk(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
    ) -> bool:
        """通过钉钉渠道发送通知"""
        from app.dingtalk import DingTalkWebhook, DingTalkWorkNotice, build_dingtalk_markdown

        markdown_text = build_dingtalk_markdown(title, content)
        sent = False

        # 优先使用工作通知（精准推送到个人）
        if await DingTalkWorkNotice.is_configured_async():
            from core.user.model import User
            stmt = select(User.dingtalk_unionid).where(
                User.id.in_(recipient_ids),
                User.dingtalk_unionid.isnot(None),
                User.dingtalk_unionid != "",
            )
            result = await db.execute(stmt)
            union_ids = [row[0] for row in result.all()]

            if union_ids:
                # 钉钉工作通知 API 的 userid_list 需要钉钉 userId
                # unionId 转 userId 需要额外 API 调用
                user_ids = await NotifyService._convert_dingtalk_unionids(union_ids)
                if user_ids:
                    success = await DingTalkWorkNotice.send_markdown(
                        userid_list=user_ids,
                        title=title,
                        text=markdown_text,
                    )
                    if success:
                        sent = True
                        logger.info(f"钉钉工作通知发送成功: {len(user_ids)} 人")

        # 回退到 Webhook 群通知
        if not sent and await DingTalkWebhook.is_configured_async():
            # 查询收件人手机号用于 @
            from core.user.model import User
            stmt = select(User.mobile).where(
                User.id.in_(recipient_ids),
                User.mobile.isnot(None),
                User.mobile != "",
            )
            result = await db.execute(stmt)
            mobiles = [row[0] for row in result.all()]

            success = await DingTalkWebhook.send_markdown(
                title=title,
                text=markdown_text,
                at_mobiles=mobiles,
            )
            if success:
                sent = True

        if not sent:
            logger.warning("钉钉通知未配置或发送失败")
            return False

        return True

    @staticmethod
    async def _convert_dingtalk_unionids(union_ids: List[str]) -> List[str]:
        """将钉钉 unionId 转换为 userId"""
        from app.dingtalk import DingTalkWorkNotice

        token = await DingTalkWorkNotice._get_access_token()
        if not token:
            return []

        user_ids = []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                for union_id in union_ids:
                    try:
                        resp = await client.post(
                            "https://oapi.dingtalk.com/topapi/user/getbyunionid",
                            params={"access_token": token},
                            json={"unionid": union_id},
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        if result.get("errcode") == 0:
                            uid = result.get("result", {}).get("userid")
                            if uid:
                                user_ids.append(uid)
                    except Exception as e:
                        logger.warning(f"钉钉 unionId 转 userId 失败 [{union_id}]: {e}")
        except Exception as e:
            logger.error(f"钉钉 unionId 批量转换异常: {e}")

        return user_ids

    @staticmethod
    async def _send_feishu(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
    ) -> bool:
        """通过飞书渠道发送通知"""
        from app.feishu import FeishuWebhook, FeishuAppMessage, build_feishu_notification_text

        notification_text = build_feishu_notification_text(title, content)
        sent = False

        # 优先使用应用消息（精准推送到个人）
        if await FeishuAppMessage.is_configured_async():
            from core.user.model import User
            stmt = select(User.feishu_union_id).where(
                User.id.in_(recipient_ids),
                User.feishu_union_id.isnot(None),
                User.feishu_union_id != "",
            )
            result = await db.execute(stmt)
            union_ids = [row[0] for row in result.all()]

            if union_ids:
                # union_id 转 open_id
                id_map = await FeishuAppMessage.get_open_ids_by_union_ids(union_ids)
                open_ids = list(id_map.values())

                if open_ids:
                    success = await FeishuAppMessage.send_batch_text(
                        open_ids=open_ids,
                        text=notification_text,
                    )
                    if success:
                        sent = True
                        logger.info(f"飞书应用消息发送成功: {len(open_ids)} 人")

        # 回退到 Webhook 群通知
        if not sent and await FeishuWebhook.is_configured_async():
            success = await FeishuWebhook.send_interactive(
                title=title,
                content=content,
            )
            if success:
                sent = True

        if not sent:
            logger.warning("飞书通知未配置或发送失败")
            return False

        return True

    @staticmethod
    async def _send_wecom(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
    ) -> bool:
        """通过企业微信渠道发送通知"""
        from app.wecom import WecomWebhook, WecomAppMessage, build_wecom_markdown

        markdown_text = build_wecom_markdown(title, content)
        sent = False

        # 优先使用应用消息（精准推送到个人）
        if await WecomAppMessage.is_configured_async():
            from core.user.model import User
            stmt = select(User.wecom_userid).where(
                User.id.in_(recipient_ids),
                User.wecom_userid.isnot(None),
                User.wecom_userid != "",
            )
            result = await db.execute(stmt)
            wecom_userids = [row[0] for row in result.all()]

            if wecom_userids:
                success = await WecomAppMessage.send_markdown(
                    userid_list=wecom_userids,
                    content=markdown_text,
                )
                if success:
                    sent = True
                    logger.info(f"企业微信应用消息发送成功: {len(wecom_userids)} 人")

        # 回退到 Webhook 群通知
        if not sent and await WecomWebhook.is_configured_async():
            success = await WecomWebhook.send_markdown(content=markdown_text)
            if success:
                sent = True

        if not sent:
            logger.warning("企业微信通知未配置或发送失败")
            return False

        return True

    @staticmethod
    async def _send_wechat_mp(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
    ) -> bool:
        """通过微信公众号模板消息渠道发送通知"""
        from app.wechat import WechatMPMessage

        if not await WechatMPMessage.is_configured_async():
            logger.warning("微信公众号模板消息未配置，跳过发送")
            return False

        # 查询用户的微信 openid
        from core.user.model import User
        stmt = select(User.wechat_openid).where(
            User.id.in_(recipient_ids),
            User.wechat_openid.isnot(None),
            User.wechat_openid != "",
        )
        result = await db.execute(stmt)
        openids = [row[0] for row in result.all()]

        if not openids:
            logger.warning("没有用户绑定微信公众号，跳过发送")
            return False

        success_count = await WechatMPMessage.batch_send_notification(
            openids=openids,
            title=title,
            content=content,
        )
        logger.info(f"微信公众号模板消息发送完成: {success_count}/{len(openids)} 成功")
        return success_count > 0

    @staticmethod
    async def _send_sms(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
    ) -> bool:
        """通过短信渠道发送通知"""
        from app.sms import SMSSender

        if not await SMSSender.is_configured_async():
            logger.warning("短信服务未配置，跳过发送")
            return False

        # 查询收件人手机号
        from core.user.model import User
        stmt = select(User.id, User.mobile).where(
            User.id.in_(recipient_ids),
            User.mobile.isnot(None),
            User.mobile != "",
        )
        result = await db.execute(stmt)
        user_mobiles = {str(row[0]): row[1] for row in result.all()}

        if not user_mobiles:
            logger.info("没有收件人配置了手机号，跳过短信发送")
            return True

        phone_list = list(user_mobiles.values())
        send_results = await SMSSender.send(
            phone_numbers=phone_list,
            title=title,
            content=content,
        )

        success_count = sum(1 for v in send_results.values() if v)
        fail_count = len(send_results) - success_count
        logger.info(f"短信发送完成: 成功 {success_count}, 失败 {fail_count}")

        return fail_count == 0

    @staticmethod
    async def _send_chat(
            db: AsyncSession,
            recipient_ids: List[str],
            title: str,
            content: str,
            link_type: str = "",
            link_id: str = "",
    ) -> bool:
        """通过聊天渠道发送通知（以系统通知用户身份发送单聊消息）"""
        from core.chat.service import ChatMessageService

        success_count = 0

        for recipient_id in recipient_ids:
            try:
                msg = await ChatMessageService.send_system_notification(
                    db=db,
                    recipient_id=recipient_id,
                    title=title,
                    content=content,
                    link_type=link_type,
                    link_id=link_id,
                )
                if msg:
                    success_count += 1
            except Exception as e:
                logger.error(f"聊天通知发送失败: recipient={recipient_id}, {e}")

        logger.info(f"聊天通知发送完成: 成功 {success_count}/{len(recipient_ids)}")
        return success_count > 0
