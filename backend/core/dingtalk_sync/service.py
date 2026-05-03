#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉组织架构同步服务
实现部门和用户从钉钉到本系统的单向同步
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
from core.dingtalk_sync.client import DingtalkClient
from core.dingtalk_sync.model import DingtalkSyncLog
from core.user.model import User
from core.user.service import UserService

logger = logging.getLogger(__name__)


def _generate_random_password(length: int = 16) -> str:
    """生成随机密码"""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(length))


class DingtalkSyncService:
    """钉钉组织架构同步服务"""

    @staticmethod
    def _is_masked(value: Optional[str]) -> bool:
        """判断值是否为脱敏值"""
        return bool(value and "***" in value)

    @staticmethod
    async def _get_client() -> DingtalkClient:
        """从配置获取钉钉客户端"""
        config = await config_manager.get_group("sync_dingtalk")
        app_key = config.get("app_key")
        app_secret = config.get("app_secret")
        if not app_key or not app_secret:
            raise ValueError("钉钉同步凭证未配置（app_key/app_secret）")
        return DingtalkClient(app_key=app_key, app_secret=app_secret)

    @staticmethod
    async def _get_sync_config() -> Dict[str, Any]:
        """获取同步配置"""
        return await config_manager.get_group("sync_dingtalk")

    @classmethod
    async def _resolve_client(cls, app_key: str = None, app_secret: str = None) -> DingtalkClient:
        """解析客户端凭证：有效明文直接用，脱敏值或空值从数据库获取"""
        use_input = (
            app_key and app_secret
            and not cls._is_masked(app_key)
            and not cls._is_masked(app_secret)
        )
        if use_input:
            return DingtalkClient(app_key=app_key, app_secret=app_secret)
        return await cls._get_client()

    # ==================== 连接测试 ====================

    @classmethod
    async def test_connection(cls, app_key: str = None, app_secret: str = None) -> Dict[str, Any]:
        """
        测试钉钉连接
        可传入临时凭证测试（保存前），也可使用已保存的配置
        """
        client = await cls._resolve_client(app_key, app_secret)
        return await client.test_connection()

    # ==================== 部门树（供前端选择范围） ====================

    @classmethod
    async def get_dingtalk_dept_tree(
        cls,
        app_key: str = None,
        app_secret: str = None,
    ) -> List[Dict[str, Any]]:
        """获取钉钉部门树（用于前端选择同步范围）"""
        client = await cls._resolve_client(app_key, app_secret)

        root_detail = await client.get_dept_detail(1)
        children = await client.get_dept_tree(1)
        return [{
            "dept_id": 1,
            "name": root_detail.get("name", "根部门"),
            "children": children,
        }]

    # ==================== 部门同步 ====================

    @classmethod
    async def sync_departments(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        全量同步钉钉部门到本系统

        流程：
        1. 从钉钉拉取指定根部门下的全量部门
        2. 按层级顺序处理，通过 dingtalk_dept_id 匹配本地 Dept
        3. 已存在则更新，不存在则创建
        """
        config = await cls._get_sync_config()
        sync_dept_id = int(config.get("sync_dept_id") or 1)
        sync_root_dept_id = config.get("sync_root_dept_id") or None

        client = await cls._get_client()

        log = DingtalkSyncLog(
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

            root_detail["parent_dept_id"] = None
            all_dingtalk_depts = [root_detail] + all_depts
            total_count = len(all_dingtalk_depts)

            # dingtalk_dept_id -> 本地 dept_id 映射
            dt_to_local: Dict[int, str] = {}

            for dt_dept in all_dingtalk_depts:
                dt_dept_id = dt_dept.get("dept_id")
                dt_name = dt_dept.get("name", "")
                dt_parent_id = dt_dept.get("parent_dept_id") or dt_dept.get("parent_id")

                try:
                    # 查找本地是否已有该部门
                    result = await db.execute(
                        select(Dept).where(
                            Dept.dingtalk_dept_id == str(dt_dept_id),
                            Dept.is_deleted == False,  # noqa: E712
                        )
                    )
                    local_dept = result.scalar_one_or_none()

                    # 确定父部门
                    if dt_dept_id == sync_dept_id:
                        parent_id = sync_root_dept_id
                    elif dt_parent_id and int(dt_parent_id) in dt_to_local:
                        parent_id = dt_to_local[int(dt_parent_id)]
                    elif dt_parent_id == sync_dept_id and sync_root_dept_id:
                        # 根部门映射到选中的本地部门
                        parent_id = dt_to_local.get(sync_dept_id, sync_root_dept_id)
                    else:
                        parent_id = None

                    # 计算 level 和 path
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
                        local_dept.name = dt_name
                        local_dept.parent_id = parent_id
                        local_dept.level = level
                        local_dept.path = path
                    else:
                        local_dept = Dept(
                            name=dt_name,
                            dingtalk_dept_id=str(dt_dept_id),
                            parent_id=parent_id,
                            level=level,
                            path=path,
                            dept_type="department",
                            status=True,
                        )
                        db.add(local_dept)

                    await db.flush()
                    dt_to_local[dt_dept_id] = local_dept.id
                    success_count += 1

                except Exception as e:
                    logger.error(f"同步部门失败 dept_id={dt_dept_id}: {e}")
                    errors.append({"dept_id": dt_dept_id, "name": dt_name, "error": str(e)})

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
        全量同步钉钉用户到本系统

        流程：
        1. 遍历已同步的所有部门（有 dingtalk_dept_id 的）
        2. 拉取每个部门下的用户
        3. 通过 dingtalk_userid 匹配，已有则更新，不存在则创建
        """
        client = await cls._get_client()

        log = DingtalkSyncLog(
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
            # 获取所有已同步的部门
            result = await db.execute(
                select(Dept).where(
                    Dept.dingtalk_dept_id.isnot(None),
                    Dept.is_deleted == False,  # noqa: E712
                )
            )
            local_depts = result.scalars().all()

            # 构建 dingtalk_dept_id -> local_dept_id 映射
            dt_dept_map = {dept.dingtalk_dept_id: dept.id for dept in local_depts}

            for dept in local_depts:
                try:
                    dt_dept_id = int(dept.dingtalk_dept_id)
                    users = await client.get_all_users_in_dept(dt_dept_id)

                    for dt_user in users:
                        dt_userid = dt_user.get("userid")
                        if not dt_userid or dt_userid in processed_userids:
                            continue

                        processed_userids.add(dt_userid)
                        total_count += 1

                        try:
                            await cls._upsert_user(db, dt_user, dt_dept_map)
                            success_count += 1
                        except Exception as e:
                            logger.error(f"同步用户失败 userid={dt_userid}: {e}")
                            errors.append({
                                "userid": dt_userid,
                                "name": dt_user.get("name", ""),
                                "error": str(e),
                            })

                except Exception as e:
                    logger.error(f"拉取部门用户失败 dept={dept.dingtalk_dept_id}: {e}")
                    errors.append({
                        "dept_id": dept.dingtalk_dept_id,
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
        dt_user: Dict[str, Any],
        dt_dept_map: Dict[str, str],
    ) -> None:
        """新增或更新单个用户"""
        dt_userid = dt_user.get("userid")
        dt_unionid = dt_user.get("unionid")
        name = dt_user.get("name", "")
        mobile = dt_user.get("mobile", "")
        email = dt_user.get("email", "")
        avatar = dt_user.get("avatar", "")
        job_number = dt_user.get("job_number", "")
        title = dt_user.get("title", "")
        active = dt_user.get("active", True)

        # 用户所属主部门
        dept_ids = dt_user.get("dept_id_list", [])
        local_dept_id = None
        if dept_ids:
            for did in dept_ids:
                mapped = dt_dept_map.get(str(did))
                if mapped:
                    local_dept_id = mapped
                    break

        # 先按 dingtalk_userid 匹配
        result = await db.execute(
            select(User).where(
                User.dingtalk_userid == dt_userid,
                User.is_deleted == False,  # noqa: E712
            )
        )
        local_user = result.scalar_one_or_none()

        # 再按 dingtalk_unionid 匹配
        if not local_user and dt_unionid:
            result = await db.execute(
                select(User).where(
                    User.dingtalk_unionid == dt_unionid,
                    User.is_deleted == False,  # noqa: E712
                )
            )
            local_user = result.scalar_one_or_none()

        # 再按手机号匹配
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
            if dt_unionid:
                local_user.dingtalk_unionid = dt_unionid
            local_user.user_status = 1 if active else 0
            local_user.is_active = active
        else:
            username = job_number or mobile or f"dt_{dt_userid}"

            # 检查 username 是否已存在
            existing = await db.execute(
                select(User).where(User.username == username)
            )
            if existing.scalar_one_or_none():
                username = f"dt_{dt_userid}"

            local_user = User(
                username=username,
                password=UserService.hash_password(_generate_random_password()),
                name=name,
                mobile=mobile or None,
                email=email or None,
                dept_id=local_dept_id,
                dingtalk_userid=dt_userid,
                dingtalk_unionid=dt_unionid or None,
                user_type=1,
                user_status=1 if active else 0,
                is_active=active,
            )
            db.add(local_user)

        await db.flush()

    # ==================== 同步统计 ====================

    @classmethod
    async def get_sync_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """获取最新的同步统计数据（分 dept/user 各取最新一条日志）"""
        stats = {}
        for sync_type in ("dept", "user"):
            result = await db.execute(
                select(DingtalkSyncLog)
                .where(
                    DingtalkSyncLog.sync_type == sync_type,
                    DingtalkSyncLog.is_deleted == False,  # noqa: E712
                )
                .order_by(desc(DingtalkSyncLog.sys_create_datetime))
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
            select(DingtalkSyncLog)
            .where(DingtalkSyncLog.is_deleted == False)  # noqa: E712
            .order_by(desc(DingtalkSyncLog.sys_create_datetime))
            .offset(offset)
            .limit(page_size)
        )
        logs = result.scalars().all()

        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count(DingtalkSyncLog.id)).where(
                DingtalkSyncLog.is_deleted == False  # noqa: E712
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

    # 订阅的通讯录事件类型
    CALLBACK_TAGS = [
        "org_dept_create",
        "org_dept_modify",
        "org_dept_remove",
        "user_add_org",
        "user_modify_org",
        "user_leave_org",
        "user_active_org",
    ]

    @classmethod
    async def register_callback(cls) -> Dict[str, Any]:
        """
        向钉钉注册事件回调

        需要配置中已填写 callback_token、callback_aes_key
        callback_url 由后端根据 APP_HOST 等设置自动生成
        """
        config = await cls._get_sync_config()
        callback_token = config.get("callback_token")
        callback_aes_key = config.get("callback_aes_key")
        if not callback_token or not callback_aes_key:
            raise ValueError("请先配置 回调Token 和 回调AES Key")

        callback_url = config.get("callback_url")
        if not callback_url:
            raise ValueError("请先配置回调地址（callback_url）")

        client = await cls._get_client()

        # 先查询是否已注册，如果已注册则走更新
        existing = await client.get_callback()
        if existing.get("errcode") == 0 and existing.get("url"):
            result = await client.update_callback(
                callback_url=callback_url,
                callback_tag=cls.CALLBACK_TAGS,
                token=callback_token,
                aes_key=callback_aes_key,
            )
        else:
            result = await client.register_callback(
                callback_url=callback_url,
                callback_tag=cls.CALLBACK_TAGS,
                token=callback_token,
                aes_key=callback_aes_key,
            )

        return {
            "success": True,
            "callback_url": callback_url,
            "subscribed_events": cls.CALLBACK_TAGS,
        }

    @classmethod
    async def delete_callback(cls) -> None:
        """删除已注册的钉钉事件回调"""
        client = await cls._get_client()
        await client.delete_callback()

    @classmethod
    async def get_callback_status(cls) -> Dict[str, Any]:
        """查询当前回调注册状态"""
        client = await cls._get_client()
        result = await client.get_callback()

        if result.get("errcode") == 0 and result.get("url"):
            return {
                "registered": True,
                "callback_url": result.get("url", ""),
                "subscribed_events": result.get("call_back_tag", []),
            }
        return {"registered": False}
