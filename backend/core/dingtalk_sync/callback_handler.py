#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉回调事件处理器

处理钉钉事件订阅推送的增量变更事件：
- 部门：org_dept_create / org_dept_modify / org_dept_remove
- 用户：user_add_org / user_modify_org / user_leave_org / user_active_org
"""
import logging
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config_manager import config_manager
from app.database import AsyncSessionLocal
from core.dept.model import Dept
from core.dingtalk_sync.client import DingtalkClient
from core.dingtalk_sync.crypto import DingtalkCrypto
from core.user.model import User
from core.user.service import UserService

logger = logging.getLogger(__name__)

# 部门事件
DEPT_EVENTS = {"org_dept_create", "org_dept_modify", "org_dept_remove"}
# 用户事件
USER_EVENTS = {"user_add_org", "user_modify_org", "user_leave_org", "user_active_org"}


class DingtalkCallbackHandler:
    """钉钉回调事件处理器"""

    @classmethod
    async def get_crypto(cls) -> DingtalkCrypto:
        """从配置获取加解密实例"""
        config = await config_manager.get_group("sync_dingtalk")
        token = config.get("callback_token")
        aes_key = config.get("callback_aes_key")
        corp_id = config.get("corp_id")
        if not all([token, aes_key, corp_id]):
            raise ValueError("钉钉回调配置不完整（callback_token / callback_aes_key / corp_id）")
        return DingtalkCrypto(token=token, aes_key=aes_key, corp_id=corp_id)

    @classmethod
    async def get_client(cls) -> DingtalkClient:
        """从配置获取钉钉客户端"""
        config = await config_manager.get_group("sync_dingtalk")
        app_key = config.get("app_key")
        app_secret = config.get("app_secret")
        if not app_key or not app_secret:
            raise ValueError("钉钉同步凭证未配置")
        return DingtalkClient(app_key=app_key, app_secret=app_secret)

    @classmethod
    async def handle_event(cls, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        分发事件到对应处理方法

        event_data 格式因事件类型不同而异，通常包含变更对象的 ID 列表
        """
        config = await config_manager.get_group("sync_dingtalk")
        enable_dept = config.get("enable_dept_event") == "true"
        enable_user = config.get("enable_user_event") == "true"

        if event_type in DEPT_EVENTS and enable_dept:
            await cls._handle_dept_event(event_type, event_data)
        elif event_type in USER_EVENTS and enable_user:
            await cls._handle_user_event(event_type, event_data)
        elif event_type == "check_url":
            pass  # 注册回调时的验证请求，不需要处理
        else:
            logger.info(f"忽略未处理的事件: {event_type}")

    # ==================== 部门事件 ====================

    @classmethod
    async def _handle_dept_event(cls, event_type: str, event_data: Dict[str, Any]) -> None:
        """处理部门变更事件"""
        dept_ids: List[int] = event_data.get("DeptId", [])
        if not dept_ids:
            logger.warning(f"部门事件缺少 DeptId: {event_data}")
            return

        client = await cls.get_client()

        async with AsyncSessionLocal() as db:
            for dept_id in dept_ids:
                try:
                    if event_type == "org_dept_remove":
                        await cls._remove_dept(db, dept_id)
                    else:
                        await cls._upsert_dept(db, client, dept_id)
                except Exception as e:
                    logger.error(f"处理部门事件失败 dept_id={dept_id}: {e}")

            await db.commit()

    @classmethod
    async def _upsert_dept(cls, db: AsyncSession, client: DingtalkClient, dt_dept_id: int) -> None:
        """创建或更新单个部门"""
        detail = await client.get_dept_detail(dt_dept_id)
        name = detail.get("name", "")
        dt_parent_id = detail.get("parent_id")

        # 查找本地部门
        result = await db.execute(
            select(Dept).where(
                Dept.dingtalk_dept_id == str(dt_dept_id),
                Dept.is_deleted == False,  # noqa: E712
            )
        )
        local_dept = result.scalar_one_or_none()

        # 查找父部门
        parent_id = None
        level = 0
        path = "/"
        if dt_parent_id:
            parent_result = await db.execute(
                select(Dept).where(
                    Dept.dingtalk_dept_id == str(dt_parent_id),
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
                dingtalk_dept_id=str(dt_dept_id),
                parent_id=parent_id,
                level=level,
                path=path,
                dept_type="department",
                status=True,
            )
            db.add(local_dept)

        await db.flush()
        logger.info(f"部门同步成功: {name} (dingtalk_dept_id={dt_dept_id})")

    @classmethod
    async def _remove_dept(cls, db: AsyncSession, dt_dept_id: int) -> None:
        """软删除部门"""
        result = await db.execute(
            select(Dept).where(
                Dept.dingtalk_dept_id == str(dt_dept_id),
                Dept.is_deleted == False,  # noqa: E712
            )
        )
        local_dept = result.scalar_one_or_none()
        if local_dept:
            local_dept.is_deleted = True
            logger.info(f"部门已删除: {local_dept.name} (dingtalk_dept_id={dt_dept_id})")
        else:
            logger.info(f"部门不存在，跳过删除: dingtalk_dept_id={dt_dept_id}")

    # ==================== 用户事件 ====================

    @classmethod
    async def _handle_user_event(cls, event_type: str, event_data: Dict[str, Any]) -> None:
        """处理用户变更事件"""
        user_ids: List[str] = event_data.get("UserId", [])
        if not user_ids:
            logger.warning(f"用户事件缺少 UserId: {event_data}")
            return

        client = await cls.get_client()

        async with AsyncSessionLocal() as db:
            # 构建 dingtalk_dept_id -> local_dept_id 映射
            dept_result = await db.execute(
                select(Dept).where(
                    Dept.dingtalk_dept_id.isnot(None),
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            local_depts = dept_result.scalars().all()
            dt_dept_map = {dept.dingtalk_dept_id: dept.id for dept in local_depts}

            for userid in user_ids:
                try:
                    if event_type == "user_leave_org":
                        await cls._deactivate_user(db, userid)
                    else:
                        await cls._upsert_user(db, client, userid, dt_dept_map)
                except Exception as e:
                    logger.error(f"处理用户事件失败 userid={userid}: {e}")

            await db.commit()

    @classmethod
    async def _upsert_user(
        cls,
        db: AsyncSession,
        client: DingtalkClient,
        dt_userid: str,
        dt_dept_map: Dict[str, str],
    ) -> None:
        """创建或更新单个用户"""
        import secrets
        import string

        detail = await client.get_user_detail(dt_userid)
        name = detail.get("name", "")
        mobile = detail.get("mobile", "")
        email = detail.get("email", "")
        unionid = detail.get("unionid")
        job_number = detail.get("job_number", "")
        active = detail.get("active", True)
        dept_ids = detail.get("dept_id_list", [])

        # 用户所属主部门
        local_dept_id = None
        for did in dept_ids:
            mapped = dt_dept_map.get(str(did))
            if mapped:
                local_dept_id = mapped
                break

        # 按 dingtalk_userid 匹配
        result = await db.execute(
            select(User).where(
                User.dingtalk_userid == dt_userid,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()

        # 按 unionid 匹配
        if not local_user and unionid:
            result = await db.execute(
                select(User).where(
                    User.dingtalk_unionid == unionid,
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

        if local_user:
            local_user.name = name
            if mobile:
                local_user.mobile = mobile
            if email:
                local_user.email = email
            if local_dept_id:
                local_user.dept_id = local_dept_id
            local_user.dingtalk_userid = dt_userid
            if unionid:
                local_user.dingtalk_unionid = unionid
            local_user.user_status = 1 if active else 0
            local_user.is_active = active
        else:
            username = job_number or mobile or f"dt_{dt_userid}"
            existing = await db.execute(select(User).where(User.username == username))
            if existing.scalar_one_or_none():
                username = f"dt_{dt_userid}"

            chars = string.ascii_letters + string.digits + "!@#$%"
            password = "".join(secrets.choice(chars) for _ in range(16))

            local_user = User(
                username=username,
                password=UserService.hash_password(password),
                name=name,
                mobile=mobile or None,
                email=email or None,
                dept_id=local_dept_id,
                dingtalk_userid=dt_userid,
                dingtalk_unionid=unionid or None,
                user_type=1,
                user_status=1 if active else 0,
                is_active=active,
            )
            db.add(local_user)

        await db.flush()
        logger.info(f"用户同步成功: {name} (dingtalk_userid={dt_userid})")

    @classmethod
    async def _deactivate_user(cls, db: AsyncSession, dt_userid: str) -> None:
        """用户离职：禁用用户"""
        result = await db.execute(
            select(User).where(
                User.dingtalk_userid == dt_userid,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()
        if local_user:
            local_user.user_status = 0
            local_user.is_active = False
            logger.info(f"用户已禁用: {local_user.name} (dingtalk_userid={dt_userid})")
        else:
            logger.info(f"用户不存在，跳过禁用: dingtalk_userid={dt_userid}")
