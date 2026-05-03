#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业微信回调事件处理器

处理企业微信事件订阅推送的增量变更事件：
- 部门：create_party / update_party / delete_party
- 成员：create_user / update_user / delete_user
"""
import logging
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config_manager import config_manager
from app.database import AsyncSessionLocal
from core.dept.model import Dept
from core.user.model import User
from core.user.service import UserService
from core.wecom_sync.client import WecomClient
from core.wecom_sync.crypto import WecomCrypto

logger = logging.getLogger(__name__)

DEPT_EVENTS = {"create_party", "update_party", "delete_party"}
USER_EVENTS = {"create_user", "update_user", "delete_user"}


class WecomCallbackHandler:
    """企业微信回调事件处理器"""

    @classmethod
    async def get_crypto(cls) -> WecomCrypto:
        """从配置获取加解密实例"""
        config = await config_manager.get_group("sync_wecom")
        token = config.get("callback_token")
        aes_key = config.get("callback_aes_key")
        corp_id = config.get("corp_id")
        if not all([token, aes_key, corp_id]):
            raise ValueError("企业微信回调配置不完整（callback_token / callback_aes_key / corp_id）")
        return WecomCrypto(token=token, aes_key=aes_key, corp_id=corp_id)

    @classmethod
    async def get_client(cls) -> WecomClient:
        """从配置获取企业微信客户端"""
        config = await config_manager.get_group("sync_wecom")
        corp_id = config.get("corp_id")
        corp_secret = config.get("corp_secret")
        if not corp_id or not corp_secret:
            raise ValueError("企业微信同步凭证未配置")
        return WecomClient(corp_id=corp_id, corp_secret=corp_secret)

    @classmethod
    async def handle_event(cls, event_type: str, event_data: Dict[str, Any]) -> None:
        """分发事件到对应处理方法"""
        config = await config_manager.get_group("sync_wecom")
        enable_dept = config.get("enable_dept_event") == "true"
        enable_user = config.get("enable_user_event") == "true"

        if event_type in DEPT_EVENTS and enable_dept:
            await cls._handle_dept_event(event_type, event_data)
        elif event_type in USER_EVENTS and enable_user:
            await cls._handle_user_event(event_type, event_data)
        else:
            logger.info(f"忽略未处理的事件: {event_type}")

    # ==================== 部门事件 ====================

    @classmethod
    async def _handle_dept_event(cls, event_type: str, event_data: Dict[str, Any]) -> None:
        """处理部门变更事件"""
        dept_id = event_data.get("Id")
        if not dept_id:
            logger.warning(f"部门事件缺少 Id: {event_data}")
            return

        client = await cls.get_client()

        async with AsyncSessionLocal() as db:
            try:
                if event_type == "delete_party":
                    await cls._remove_dept(db, int(dept_id))
                else:
                    await cls._upsert_dept(db, client, int(dept_id))
            except Exception as e:
                logger.error(f"处理部门事件失败 dept_id={dept_id}: {e}")

            await db.commit()

    @classmethod
    async def _upsert_dept(cls, db: AsyncSession, client: WecomClient, wecom_dept_id: int) -> None:
        """创建或更新单个部门"""
        detail = await client.get_dept_detail(wecom_dept_id)
        name = detail.get("name", "")
        wecom_parent_id = detail.get("parentid")

        result = await db.execute(
            select(Dept).where(
                Dept.wecom_dept_id == str(wecom_dept_id),
                Dept.is_deleted == False,  # noqa: E712
            )
        )
        local_dept = result.scalar_one_or_none()

        parent_id = None
        level = 0
        path = "/"
        if wecom_parent_id:
            parent_result = await db.execute(
                select(Dept).where(
                    Dept.wecom_dept_id == str(wecom_parent_id),
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
                wecom_dept_id=str(wecom_dept_id),
                parent_id=parent_id,
                level=level,
                path=path,
                dept_type="department",
                status=True,
            )
            db.add(local_dept)

        await db.flush()
        logger.info(f"部门同步成功: {name} (wecom_dept_id={wecom_dept_id})")

    @classmethod
    async def _remove_dept(cls, db: AsyncSession, wecom_dept_id: int) -> None:
        """软删除部门"""
        result = await db.execute(
            select(Dept).where(
                Dept.wecom_dept_id == str(wecom_dept_id),
                Dept.is_deleted == False,  # noqa: E712
            )
        )
        local_dept = result.scalar_one_or_none()
        if local_dept:
            local_dept.is_deleted = True
            logger.info(f"部门已删除: {local_dept.name} (wecom_dept_id={wecom_dept_id})")

    # ==================== 用户事件 ====================

    @classmethod
    async def _handle_user_event(cls, event_type: str, event_data: Dict[str, Any]) -> None:
        """处理用户变更事件"""
        userid = event_data.get("UserID")
        if not userid:
            logger.warning(f"用户事件缺少 UserID: {event_data}")
            return

        new_userid = event_data.get("NewUserID")

        client = await cls.get_client()

        async with AsyncSessionLocal() as db:
            dept_result = await db.execute(
                select(Dept).where(
                    Dept.wecom_dept_id.isnot(None),
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            local_depts = dept_result.scalars().all()
            wecom_dept_map = {dept.wecom_dept_id: dept.id for dept in local_depts}

            try:
                if event_type == "delete_user":
                    await cls._deactivate_user(db, userid)
                elif event_type == "update_user" and new_userid:
                    await cls._update_userid(db, userid, new_userid)
                    await cls._upsert_user(db, client, new_userid, wecom_dept_map)
                else:
                    await cls._upsert_user(db, client, userid, wecom_dept_map)
            except Exception as e:
                logger.error(f"处理用户事件失败 userid={userid}: {e}")

            await db.commit()

    @classmethod
    async def _upsert_user(
        cls,
        db: AsyncSession,
        client: WecomClient,
        wecom_userid: str,
        wecom_dept_map: Dict[str, str],
    ) -> None:
        """创建或更新单个用户"""
        import secrets
        import string

        detail = await client.get_user_detail(wecom_userid)
        name = detail.get("name", "")
        mobile = detail.get("mobile", "")
        email = detail.get("email", "")
        status = detail.get("status", 1)
        dept_ids = detail.get("department", [])

        local_dept_id = None
        main_department = detail.get("main_department")
        if main_department and str(main_department) in wecom_dept_map:
            local_dept_id = wecom_dept_map[str(main_department)]
        else:
            for did in dept_ids:
                mapped = wecom_dept_map.get(str(did))
                if mapped:
                    local_dept_id = mapped
                    break

        # 按 wecom_userid 匹配
        result = await db.execute(
            select(User).where(
                User.wecom_userid == wecom_userid,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()

        # 按手机号匹配
        if not local_user and mobile:
            result = await db.execute(
                select(User).where(
                    User.mobile == mobile,
                    User.is_deleted == False,  # noqa: E712
                )
            )
            local_user = result.scalar_one_or_none()

        active = status == 1

        if local_user:
            local_user.name = name
            if mobile:
                local_user.mobile = mobile
            if email:
                local_user.email = email
            if local_dept_id:
                local_user.dept_id = local_dept_id
            local_user.wecom_userid = wecom_userid
            local_user.user_status = 1 if active else 0
            local_user.is_active = active
        else:
            username = mobile or f"wc_{wecom_userid}"
            existing = await db.execute(select(User).where(User.username == username))
            if existing.scalar_one_or_none():
                username = f"wc_{wecom_userid}"

            chars = string.ascii_letters + string.digits + "!@#$%"
            password = "".join(secrets.choice(chars) for _ in range(16))

            local_user = User(
                username=username,
                password=UserService.hash_password(password),
                name=name,
                mobile=mobile or None,
                email=email or None,
                dept_id=local_dept_id,
                wecom_userid=wecom_userid,
                user_type=1,
                user_status=1 if active else 0,
                is_active=active,
            )
            db.add(local_user)

        await db.flush()
        logger.info(f"用户同步成功: {name} (wecom_userid={wecom_userid})")

    @classmethod
    async def _update_userid(cls, db: AsyncSession, old_userid: str, new_userid: str) -> None:
        """处理 userid 变更"""
        result = await db.execute(
            select(User).where(
                User.wecom_userid == old_userid,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()
        if local_user:
            local_user.wecom_userid = new_userid
            await db.flush()
            logger.info(f"用户 userid 已更新: {old_userid} -> {new_userid}")

    @classmethod
    async def _deactivate_user(cls, db: AsyncSession, wecom_userid: str) -> None:
        """用户离职：禁用用户"""
        result = await db.execute(
            select(User).where(
                User.wecom_userid == wecom_userid,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()
        if local_user:
            local_user.user_status = 0
            local_user.is_active = False
            logger.info(f"用户已禁用: {local_user.name} (wecom_userid={wecom_userid})")
