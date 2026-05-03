#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书组织架构同步服务
实现部门和用户从飞书到本系统的单向同步
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
from core.feishu_sync.client import FeishuClient
from core.feishu_sync.model import FeishuSyncLog
from core.user.model import User
from core.user.service import UserService

logger = logging.getLogger(__name__)


def _generate_random_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


class FeishuSyncService:
    """飞书组织架构同步服务"""

    @staticmethod
    def _is_masked(value: Optional[str]) -> bool:
        """判断值是否为脱敏值"""
        return bool(value and "***" in value)

    @staticmethod
    async def _get_client() -> FeishuClient:
        """从配置获取飞书客户端"""
        config = await config_manager.get_group("sync_feishu")
        app_id = config.get("app_id")
        app_secret = config.get("app_secret")
        if not app_id or not app_secret:
            raise ValueError("飞书同步凭证未配置（app_id/app_secret）")
        return FeishuClient(app_id=app_id, app_secret=app_secret)

    @staticmethod
    async def _get_sync_config() -> Dict[str, Any]:
        return await config_manager.get_group("sync_feishu")

    @classmethod
    async def _resolve_client(cls, app_id: str = None, app_secret: str = None) -> FeishuClient:
        """解析客户端凭证：有效明文直接用，脱敏值或空值从数据库获取"""
        use_input = (
            app_id and app_secret
            and not cls._is_masked(app_id)
            and not cls._is_masked(app_secret)
        )
        if use_input:
            return FeishuClient(app_id=app_id, app_secret=app_secret)
        return await cls._get_client()

    # ==================== 连接测试 ====================

    @classmethod
    async def test_connection(cls, app_id: str = None, app_secret: str = None) -> Dict[str, Any]:
        client = await cls._resolve_client(app_id, app_secret)
        return await client.test_connection()

    # ==================== 部门树（供前端选择范围） ====================

    @classmethod
    async def get_feishu_dept_tree(
        cls,
        app_id: str = None,
        app_secret: str = None,
    ) -> List[Dict[str, Any]]:
        """获取飞书部门树（用于前端选择同步范围）"""
        client = await cls._resolve_client(app_id, app_secret)

        root_detail = await client.get_dept_detail("0")
        children = await client.get_dept_tree("0")
        return [{
            "dept_id": "0",
            "name": root_detail.get("name", "根部门"),
            "children": children,
        }]

    # ==================== 部门同步 ====================

    @classmethod
    async def sync_departments(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        全量同步飞书部门到本系统

        流程：
        1. 从飞书拉取指定根部门下的全量部门
        2. 按层级顺序处理，通过 feishu_dept_id 匹配本地 Dept
        3. 已存在则更新，不存在则创建
        """
        config = await cls._get_sync_config()
        sync_dept_id = config.get("sync_dept_id") or "0"
        sync_root_dept_id = config.get("sync_root_dept_id") or None

        client = await cls._get_client()

        log = FeishuSyncLog(
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
            root_detail = await client.get_dept_detail(sync_dept_id)
            all_depts = await client.get_all_depts(sync_dept_id)

            root_detail["parent_department_id"] = None
            root_detail["open_department_id"] = sync_dept_id
            all_feishu_depts = [root_detail] + all_depts
            total_count = len(all_feishu_depts)

            # feishu_dept_id -> 本地 dept_id 映射
            fs_to_local: Dict[str, str] = {}

            for fs_dept in all_feishu_depts:
                fs_dept_id = fs_dept.get("open_department_id", "")
                fs_name = fs_dept.get("name", "")
                fs_parent_id = fs_dept.get("parent_department_id")

                try:
                    result = await db.execute(
                        select(Dept).where(
                            Dept.feishu_dept_id == fs_dept_id,
                            Dept.is_deleted == False,  # noqa: E712
                        )
                    )
                    local_dept = result.scalar_one_or_none()

                    if fs_dept_id == sync_dept_id:
                        parent_id = sync_root_dept_id
                    elif fs_parent_id and fs_parent_id in fs_to_local:
                        parent_id = fs_to_local[fs_parent_id]
                    elif fs_parent_id == sync_dept_id and sync_root_dept_id:
                        parent_id = fs_to_local.get(sync_dept_id, sync_root_dept_id)
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
                        local_dept.name = fs_name
                        local_dept.parent_id = parent_id
                        local_dept.level = level
                        local_dept.path = path
                    else:
                        local_dept = Dept(
                            name=fs_name,
                            feishu_dept_id=fs_dept_id,
                            parent_id=parent_id,
                            level=level,
                            path=path,
                            dept_type="department",
                            status=True,
                        )
                        db.add(local_dept)

                    await db.flush()
                    fs_to_local[fs_dept_id] = local_dept.id
                    success_count += 1

                except Exception as e:
                    logger.error(f"同步部门失败 dept_id={fs_dept_id}: {e}")
                    errors.append({"dept_id": fs_dept_id, "name": fs_name, "error": str(e)})

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
        """
        全量同步飞书用户到本系统

        流程：
        1. 遍历已同步的所有部门（有 feishu_dept_id 的）
        2. 拉取每个部门下的用户
        3. 通过 feishu_userid 匹配，已有则更新，不存在则创建
        """
        client = await cls._get_client()

        log = FeishuSyncLog(
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
                    Dept.feishu_dept_id.isnot(None),
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            local_depts = result.scalars().all()

            fs_dept_map = {dept.feishu_dept_id: dept.id for dept in local_depts}

            for dept in local_depts:
                try:
                    users = await client.get_all_users_in_dept(dept.feishu_dept_id)

                    for fs_user in users:
                        open_id = fs_user.get("open_id", "")
                        if not open_id or open_id in processed_userids:
                            continue

                        processed_userids.add(open_id)
                        total_count += 1

                        try:
                            await cls._upsert_user(db, fs_user, fs_dept_map)
                            success_count += 1
                        except Exception as e:
                            logger.error(f"同步用户失败 open_id={open_id}: {e}")
                            errors.append({
                                "open_id": open_id,
                                "name": fs_user.get("name", ""),
                                "error": str(e),
                            })

                except Exception as e:
                    logger.error(f"拉取部门用户失败 dept={dept.feishu_dept_id}: {e}")
                    errors.append({
                        "dept_id": dept.feishu_dept_id,
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
        fs_user: Dict[str, Any],
        fs_dept_map: Dict[str, str],
    ) -> None:
        """新增或更新单个用户"""
        open_id = fs_user.get("open_id", "")
        union_id = fs_user.get("union_id")
        name = fs_user.get("name", "")
        mobile = fs_user.get("mobile", "")
        email = fs_user.get("email", "")
        avatar_info = fs_user.get("avatar", {})
        avatar = avatar_info.get("avatar_72", "") if isinstance(avatar_info, dict) else ""
        status_info = fs_user.get("status", {})
        active = (
            status_info.get("is_activated", True)
            and not status_info.get("is_frozen", False)
            and not status_info.get("is_resigned", False)
            and not status_info.get("is_exited", False)
        )

        dept_ids = fs_user.get("department_ids", [])
        local_dept_id = None
        if dept_ids:
            for did in dept_ids:
                mapped = fs_dept_map.get(did)
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
            existing = await db.execute(
                select(User).where(User.username == username)
            )
            if existing.scalar_one_or_none():
                username = f"fs_{open_id}"

            local_user = User(
                username=username,
                password=UserService.hash_password(_generate_random_password()),
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

    # ==================== 同步统计 ====================

    @classmethod
    async def get_sync_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """获取最新的同步统计数据"""
        stats = {}
        for sync_type in ("dept", "user"):
            result = await db.execute(
                select(FeishuSyncLog)
                .where(
                    FeishuSyncLog.sync_type == sync_type,
                    FeishuSyncLog.is_deleted == False,  # noqa: E712
                )
                .order_by(desc(FeishuSyncLog.sys_create_datetime))
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

    @classmethod
    async def get_sync_logs(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取同步日志列表"""
        offset = (page - 1) * page_size
        result = await db.execute(
            select(FeishuSyncLog)
            .where(FeishuSyncLog.is_deleted == False)  # noqa: E712
            .order_by(desc(FeishuSyncLog.sys_create_datetime))
            .offset(offset)
            .limit(page_size)
        )
        logs = result.scalars().all()

        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count(FeishuSyncLog.id)).where(
                FeishuSyncLog.is_deleted == False  # noqa: E712
            )
        )
        total = count_result.scalar() or 0

        return {
            "items": [
                {
                    "id": log.id,
                    "sync_type": log.sync_type,
                    "total_count": log.total_count,
                    "success_count": log.success_count,
                    "fail_count": log.fail_count,
                    "status": log.status,
                    "error_detail": log.error_detail,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ==================== 事件回调管理 ====================

    @classmethod
    async def get_callback_status(cls) -> Dict[str, Any]:
        """查询回调配置状态（飞书回调在管理后台手动配置）"""
        config = await cls._get_sync_config()
        encrypt_key = config.get("encrypt_key", "")
        verification_token = config.get("verification_token", "")
        callback_url = config.get("callback_url", "")

        if encrypt_key and verification_token and callback_url:
            return {
                "registered": True,
                "callback_url": callback_url,
                "subscribed_events": [
                    "contact.department.created_v3",
                    "contact.department.updated_v3",
                    "contact.department.deleted_v3",
                    "contact.user.created_v3",
                    "contact.user.updated_v3",
                    "contact.user.deleted_v3",
                ],
            }
        return {"registered": False}
