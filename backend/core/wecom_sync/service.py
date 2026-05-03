#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业微信组织架构同步服务
实现部门和用户从企业微信到本系统的单向同步
"""
import json
import logging
import secrets
import string
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config_manager import config_manager
from core.dept.model import Dept
from core.user.model import User
from core.user.service import UserService
from core.wecom_sync.client import WecomClient
from core.wecom_sync.model import WecomSyncLog

logger = logging.getLogger(__name__)


def _generate_random_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


class WecomSyncService:
    """企业微信组织架构同步服务"""

    @staticmethod
    def _is_masked(value: Optional[str]) -> bool:
        """判断值是否为脱敏值"""
        return bool(value and "***" in value)

    @staticmethod
    async def _get_client() -> WecomClient:
        config = await config_manager.get_group("sync_wecom")
        corp_id = config.get("corp_id")
        corp_secret = config.get("corp_secret")
        if not corp_id or not corp_secret:
            raise ValueError("企业微信同步凭证未配置（corp_id/corp_secret）")
        return WecomClient(corp_id=corp_id, corp_secret=corp_secret)

    @staticmethod
    async def _get_sync_config() -> Dict[str, Any]:
        return await config_manager.get_group("sync_wecom")

    @classmethod
    async def _resolve_client(cls, corp_id: str = None, corp_secret: str = None) -> WecomClient:
        """解析客户端凭证：有效明文直接用，脱敏值或空值从数据库获取"""
        use_input = (
            corp_id and corp_secret
            and not cls._is_masked(corp_id)
            and not cls._is_masked(corp_secret)
        )
        if use_input:
            return WecomClient(corp_id=corp_id, corp_secret=corp_secret)
        return await cls._get_client()

    # ==================== 连接测试 ====================

    @classmethod
    async def test_connection(cls, corp_id: str = None, corp_secret: str = None) -> Dict[str, Any]:
        client = await cls._resolve_client(corp_id, corp_secret)
        return await client.test_connection()

    # ==================== 部门树 ====================

    @classmethod
    async def get_wecom_dept_tree(
        cls,
        corp_id: str = None,
        corp_secret: str = None,
    ) -> List[Dict[str, Any]]:
        client = await cls._resolve_client(corp_id, corp_secret)

        tree = await client.get_dept_tree(1)
        return tree

    # ==================== 部门同步 ====================

    @classmethod
    async def sync_departments(cls, db: AsyncSession) -> Dict[str, Any]:
        config = await cls._get_sync_config()
        sync_dept_id = int(config.get("sync_dept_id") or 1)
        sync_root_dept_id = config.get("sync_root_dept_id") or None

        client = await cls._get_client()

        log = WecomSyncLog(
            sync_type="dept",
            status="running",
            started_at=datetime.now(),
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        errors = []
        success_count = 0
        total_count = 0

        try:
            all_depts_raw = await client.get_dept_list(sync_dept_id)
            total_count = len(all_depts_raw)

            # 按 parentid 排序保证父部门先处理
            all_depts_raw.sort(key=lambda d: d.get("id", 0))

            dt_to_local: Dict[int, str] = {}

            for wecom_dept in all_depts_raw:
                wecom_dept_id = wecom_dept.get("id")
                name = wecom_dept.get("name", "")
                wecom_parent_id = wecom_dept.get("parentid")

                try:
                    result = await db.execute(
                        select(Dept).where(
                            Dept.wecom_dept_id == str(wecom_dept_id),
                            Dept.is_deleted == False,  # noqa: E712
                        )
                    )
                    local_dept = result.scalar_one_or_none()

                    if wecom_dept_id == sync_dept_id:
                        parent_id = sync_root_dept_id
                    elif wecom_parent_id and int(wecom_parent_id) in dt_to_local:
                        parent_id = dt_to_local[int(wecom_parent_id)]
                    elif wecom_parent_id == sync_dept_id and sync_root_dept_id:
                        parent_id = dt_to_local.get(sync_dept_id, sync_root_dept_id)
                    else:
                        parent_id = None

                    level = 0
                    path = "/"
                    if parent_id:
                        parent_result = await db.execute(
                            select(Dept).where(Dept.id == parent_id)
                        )
                        parent = parent_result.scalar_one_or_none()
                        if parent:
                            level = parent.level + 1
                            path = f"{parent.path or '/'}{parent.id}/"

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
                    dt_to_local[wecom_dept_id] = local_dept.id
                    success_count += 1

                except Exception as e:
                    logger.error(f"同步部门失败 dept_id={wecom_dept_id}: {e}")
                    errors.append({"dept_id": wecom_dept_id, "name": name, "error": str(e)})

            await db.commit()

            log.total_count = total_count
            log.success_count = success_count
            log.fail_count = len(errors)
            log.status = "success" if not errors else ("partial" if success_count > 0 else "failed")
            log.error_detail = json.dumps(errors, ensure_ascii=False) if errors else None
            log.finished_at = datetime.now()
            await db.commit()

        except Exception as e:
            logger.error(f"部门同步异常: {e}")
            log.status = "failed"
            log.error_detail = str(e)
            log.finished_at = datetime.now()
            log.total_count = total_count
            log.success_count = success_count
            log.fail_count = total_count - success_count
            await db.commit()
            raise

        return {
            "total": total_count,
            "success": success_count,
            "fail": len(errors),
            "status": log.status,
            "errors": errors,
        }

    # ==================== 用户同步 ====================

    @classmethod
    async def sync_users(cls, db: AsyncSession) -> Dict[str, Any]:
        client = await cls._get_client()

        log = WecomSyncLog(
            sync_type="user",
            status="running",
            started_at=datetime.now(),
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        errors = []
        success_count = 0
        total_count = 0
        processed_userids = set()

        try:
            result = await db.execute(
                select(Dept).where(
                    Dept.wecom_dept_id.isnot(None),
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            local_depts = result.scalars().all()

            wecom_dept_map = {dept.wecom_dept_id: dept.id for dept in local_depts}

            for dept in local_depts:
                try:
                    wecom_dept_id = int(dept.wecom_dept_id)
                    users = await client.get_user_list(wecom_dept_id)

                    for wecom_user in users:
                        userid = wecom_user.get("userid")
                        if not userid or userid in processed_userids:
                            continue

                        processed_userids.add(userid)
                        total_count += 1

                        try:
                            await cls._upsert_user(db, wecom_user, wecom_dept_map)
                            success_count += 1
                        except Exception as e:
                            logger.error(f"同步用户失败 userid={userid}: {e}")
                            errors.append({
                                "userid": userid,
                                "name": wecom_user.get("name", ""),
                                "error": str(e),
                            })

                except Exception as e:
                    logger.error(f"拉取部门用户失败 dept={dept.wecom_dept_id}: {e}")
                    errors.append({
                        "dept_id": dept.wecom_dept_id,
                        "error": str(e),
                    })

            await db.commit()

            log.total_count = total_count
            log.success_count = success_count
            log.fail_count = len(errors)
            log.status = "success" if not errors else ("partial" if success_count > 0 else "failed")
            log.error_detail = json.dumps(errors, ensure_ascii=False) if errors else None
            log.finished_at = datetime.now()
            await db.commit()

        except Exception as e:
            logger.error(f"用户同步异常: {e}")
            log.status = "failed"
            log.error_detail = str(e)
            log.finished_at = datetime.now()
            log.total_count = total_count
            log.success_count = success_count
            log.fail_count = total_count - success_count
            await db.commit()
            raise

        return {
            "total": total_count,
            "success": success_count,
            "fail": len(errors),
            "status": log.status,
            "errors": errors,
        }

    @classmethod
    async def _upsert_user(
        cls,
        db: AsyncSession,
        wecom_user: Dict[str, Any],
        wecom_dept_map: Dict[str, str],
    ) -> None:
        userid = wecom_user.get("userid")
        name = wecom_user.get("name", "")
        mobile = wecom_user.get("mobile", "")
        email = wecom_user.get("email", "")
        status = wecom_user.get("status", 1)

        dept_ids = wecom_user.get("department", [])
        main_department = wecom_user.get("main_department")

        local_dept_id = None
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
                User.wecom_userid == userid,
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
            local_user.wecom_userid = userid
            local_user.user_status = 1 if active else 0
            local_user.is_active = active
        else:
            username = mobile or f"wc_{userid}"
            existing = await db.execute(
                select(User).where(User.username == username)
            )
            if existing.scalar_one_or_none():
                username = f"wc_{userid}"

            local_user = User(
                username=username,
                password=UserService.hash_password(_generate_random_password()),
                name=name,
                mobile=mobile or None,
                email=email or None,
                dept_id=local_dept_id,
                wecom_userid=userid,
                user_type=1,
                user_status=1 if active else 0,
                is_active=active,
            )
            db.add(local_user)

        await db.flush()

    # ==================== 同步统计 ====================

    @classmethod
    async def get_sync_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        stats = {}
        for sync_type in ("dept", "user"):
            result = await db.execute(
                select(WecomSyncLog)
                .where(
                    WecomSyncLog.sync_type == sync_type,
                    WecomSyncLog.is_deleted == False,  # noqa: E712
                )
                .order_by(desc(WecomSyncLog.sys_create_datetime))
                .limit(1)
            )
            log = result.scalar_one_or_none()
            if log:
                stats[sync_type] = {
                    "total_count": log.total_count or 0,
                    "success_count": log.success_count or 0,
                    "fail_count": log.fail_count or 0,
                    "not_synced": max(0, (log.total_count or 0) - (log.success_count or 0) - (log.fail_count or 0)),
                    "status": log.status,
                    "sync_time": log.finished_at.isoformat() if log.finished_at else None,
                }
            else:
                stats[sync_type] = {
                    "total_count": 0,
                    "success_count": 0,
                    "fail_count": 0,
                    "not_synced": 0,
                    "status": None,
                    "sync_time": None,
                }
        return stats

    # ==================== 回调状态 ====================

    CALLBACK_TAGS = [
        "create_party",
        "update_party",
        "delete_party",
        "create_user",
        "update_user",
        "delete_user",
    ]

    @classmethod
    async def get_callback_status(cls) -> Dict[str, Any]:
        """查询回调配置状态（企业微信回调在管理后台配置，这里只检查本地配置是否完整）"""
        config = await cls._get_sync_config()
        token = config.get("callback_token")
        aes_key = config.get("callback_aes_key")
        callback_url = config.get("callback_url")

        registered = bool(token and aes_key and callback_url)
        return {
            "registered": registered,
            "callback_url": callback_url or "",
            "subscribed_events": cls.CALLBACK_TAGS if registered else [],
        }
