#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书回调事件处理器

处理飞书事件订阅推送的增量变更事件（v2.0 格式）：
- 部门：contact.department.created_v3 / contact.department.updated_v3 / contact.department.deleted_v3
- 用户：contact.user.created_v3 / contact.user.updated_v3 / contact.user.deleted_v3

飞书事件结构：
{
    "schema": "2.0",
    "header": {"event_id": "...", "event_type": "...", ...},
    "event": {"object": {...}, "old_object": {...}}
}
"""
import logging
from typing import Any, Dict, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config_manager import config_manager
from app.database import AsyncSessionLocal
from core.dept.model import Dept
from core.feishu_sync.client import FeishuClient
from core.feishu_sync.crypto import FeishuCrypto
from core.user.model import User
from core.user.service import UserService

logger = logging.getLogger(__name__)

DEPT_EVENTS = {
    "contact.department.created_v3",
    "contact.department.updated_v3",
    "contact.department.deleted_v3",
}
USER_EVENTS = {
    "contact.user.created_v3",
    "contact.user.updated_v3",
    "contact.user.deleted_v3",
}

# 简易幂等去重（进程内存级），记录已处理的 event_id
_processed_event_ids: Set[str] = set()
_MAX_EVENT_IDS = 10000


class FeishuCallbackHandler:
    """飞书回调事件处理器"""

    @classmethod
    async def get_crypto(cls) -> FeishuCrypto:
        """从配置获取加解密实例"""
        config = await config_manager.get_group("sync_feishu")
        encrypt_key = config.get("encrypt_key", "")
        verification_token = config.get("verification_token", "")
        if not encrypt_key or not verification_token:
            raise ValueError("飞书回调配置不完整（encrypt_key / verification_token）")
        return FeishuCrypto(encrypt_key=encrypt_key, verification_token=verification_token)

    @classmethod
    async def get_client(cls) -> FeishuClient:
        """从配置获取飞书客户端"""
        config = await config_manager.get_group("sync_feishu")
        app_id = config.get("app_id")
        app_secret = config.get("app_secret")
        if not app_id or not app_secret:
            raise ValueError("飞书同步凭证未配置")
        return FeishuClient(app_id=app_id, app_secret=app_secret)

    @classmethod
    def _check_idempotent(cls, event_id: str) -> bool:
        """检查 event_id 是否已处理（幂等去重），返回 True 表示已处理过"""
        global _processed_event_ids
        if event_id in _processed_event_ids:
            return True
        if len(_processed_event_ids) >= _MAX_EVENT_IDS:
            _processed_event_ids = set()
        _processed_event_ids.add(event_id)
        return False

    @classmethod
    async def handle_event(cls, event_body: Dict[str, Any]) -> None:
        """
        处理 v2.0 格式的事件

        event_body 已解密后的完整 JSON:
        {"schema":"2.0","header":{...},"event":{...}}
        """
        header = event_body.get("header", {})
        event_type = header.get("event_type", "")
        event_id = header.get("event_id", "")

        if event_id and cls._check_idempotent(event_id):
            logger.info(f"重复事件，跳过: event_id={event_id}")
            return

        config = await config_manager.get_group("sync_feishu")
        enable_dept = config.get("enable_dept_event") == "true"
        enable_user = config.get("enable_user_event") == "true"

        event = event_body.get("event", {})

        if event_type in DEPT_EVENTS and enable_dept:
            await cls._handle_dept_event(event_type, event)
        elif event_type in USER_EVENTS and enable_user:
            await cls._handle_user_event(event_type, event)
        else:
            logger.info(f"忽略未处理的事件: {event_type}")

    # ==================== 部门事件 ====================

    @classmethod
    async def _handle_dept_event(cls, event_type: str, event: Dict[str, Any]) -> None:
        """处理部门变更事件"""
        obj = event.get("object", {})
        dept_id = obj.get("open_department_id", "")

        if not dept_id:
            logger.warning(f"部门事件缺少 open_department_id: {event}")
            return

        async with AsyncSessionLocal() as db:
            try:
                if event_type == "contact.department.deleted_v3":
                    await cls._remove_dept(db, dept_id)
                else:
                    await cls._upsert_dept_from_event(db, obj)
                await db.commit()
            except Exception as e:
                logger.error(f"处理部门事件失败 dept_id={dept_id}: {e}")

    @classmethod
    async def _upsert_dept_from_event(cls, db: AsyncSession, obj: Dict[str, Any]) -> None:
        """从事件 object 创建或更新部门"""
        dept_id = obj.get("open_department_id", "")
        name = obj.get("name", "")
        parent_dept_id = obj.get("parent_department_id", "0")

        result = await db.execute(
            select(Dept).where(
                Dept.feishu_dept_id == dept_id,
                Dept.is_deleted == False,  # noqa: E712
            )
        )
        local_dept = result.scalar_one_or_none()

        parent_id = None
        level = 0
        path = "/"
        if parent_dept_id and parent_dept_id != "0":
            parent_result = await db.execute(
                select(Dept).where(
                    Dept.feishu_dept_id == parent_dept_id,
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            parent_dept = parent_result.scalar_one_or_none()
            if parent_dept:
                parent_id = parent_dept.id
                level = parent_dept.level + 1
                path = f"{parent_dept.path or '/'}{parent_dept.id}/"

        if local_dept:
            local_dept.name = name
            local_dept.parent_id = parent_id
            local_dept.level = level
            local_dept.path = path
        else:
            local_dept = Dept(
                name=name,
                feishu_dept_id=dept_id,
                parent_id=parent_id,
                level=level,
                path=path,
                dept_type="department",
                status=True,
            )
            db.add(local_dept)

        await db.flush()
        logger.info(f"部门同步成功: {name} (feishu_dept_id={dept_id})")

    @classmethod
    async def _remove_dept(cls, db: AsyncSession, feishu_dept_id: str) -> None:
        """软删除部门"""
        result = await db.execute(
            select(Dept).where(
                Dept.feishu_dept_id == feishu_dept_id,
                Dept.is_deleted == False,  # noqa: E712
            )
        )
        local_dept = result.scalar_one_or_none()
        if local_dept:
            local_dept.is_deleted = True
            logger.info(f"部门已删除: {local_dept.name} (feishu_dept_id={feishu_dept_id})")
        else:
            logger.info(f"部门不存在，跳过删除: feishu_dept_id={feishu_dept_id}")

    # ==================== 用户事件 ====================

    @classmethod
    async def _handle_user_event(cls, event_type: str, event: Dict[str, Any]) -> None:
        """处理用户变更事件"""
        obj = event.get("object", {})
        open_id = obj.get("open_id", "")

        if not open_id:
            logger.warning(f"用户事件缺少 open_id: {event}")
            return

        client = await cls.get_client()

        async with AsyncSessionLocal() as db:
            dept_result = await db.execute(
                select(Dept).where(
                    Dept.feishu_dept_id.isnot(None),
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            local_depts = dept_result.scalars().all()
            feishu_dept_map = {dept.feishu_dept_id: dept.id for dept in local_depts}

            try:
                if event_type == "contact.user.deleted_v3":
                    await cls._deactivate_user(db, open_id)
                else:
                    await cls._upsert_user(db, client, open_id, feishu_dept_map)
                await db.commit()
            except Exception as e:
                logger.error(f"处理用户事件失败 open_id={open_id}: {e}")

    @classmethod
    async def _upsert_user(
        cls,
        db: AsyncSession,
        client: FeishuClient,
        open_id: str,
        feishu_dept_map: Dict[str, str],
    ) -> None:
        """创建或更新单个用户"""
        import secrets
        import string

        detail = await client.get_user_detail(open_id)
        name = detail.get("name", "")
        mobile = detail.get("mobile", "")
        email = detail.get("email", "")
        union_id = detail.get("union_id")
        status_info = detail.get("status", {})
        active = (
            status_info.get("is_activated", True)
            and not status_info.get("is_frozen", False)
            and not status_info.get("is_resigned", False)
            and not status_info.get("is_exited", False)
        )
        dept_ids = detail.get("department_ids", [])

        local_dept_id = None
        for did in dept_ids:
            mapped = feishu_dept_map.get(did)
            if mapped:
                local_dept_id = mapped
                break

        result = await db.execute(
            select(User).where(
                User.feishu_userid == open_id,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()

        if not local_user and union_id:
            result = await db.execute(
                select(User).where(
                    User.feishu_union_id == union_id,
                    User.is_deleted == False,  # noqa: E712
                )
            )
            local_user = result.scalar_one_or_none()

        if not local_user and mobile:
            result = await db.execute(
                select(User).where(
                    User.mobile == mobile,
                    User.is_deleted == False,  # noqa: E712
                )
            )
            local_user = result.scalar_one_or_none()

        if local_user:
            local_user.name = name
            if mobile:
                local_user.mobile = mobile
            if email:
                local_user.email = email
            if local_dept_id:
                local_user.dept_id = local_dept_id
            local_user.feishu_userid = open_id
            if union_id:
                local_user.feishu_union_id = union_id
            local_user.user_status = 1 if active else 0
            local_user.is_active = active
        else:
            username = mobile or f"fs_{open_id}"
            existing = await db.execute(select(User).where(User.username == username))
            if existing.scalar_one_or_none():
                username = f"fs_{open_id}"

            chars = string.ascii_letters + string.digits + "!@#$%"
            password = "".join(secrets.choice(chars) for _ in range(16))

            local_user = User(
                username=username,
                password=UserService.hash_password(password),
                name=name,
                mobile=mobile or None,
                email=email or None,
                dept_id=local_dept_id,
                feishu_userid=open_id,
                feishu_union_id=union_id or None,
                user_type=1,
                user_status=1 if active else 0,
                is_active=active,
            )
            db.add(local_user)

        await db.flush()
        logger.info(f"用户同步成功: {name} (feishu_userid={open_id})")

    @classmethod
    async def _deactivate_user(cls, db: AsyncSession, open_id: str) -> None:
        """用户离职：禁用用户"""
        result = await db.execute(
            select(User).where(
                User.feishu_userid == open_id,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()
        if local_user:
            local_user.user_status = 0
            local_user.is_active = False
            logger.info(f"用户已禁用: {local_user.name} (feishu_userid={open_id})")
        else:
            logger.info(f"用户不存在，跳过禁用: feishu_userid={open_id}")
