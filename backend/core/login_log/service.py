#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录日志服务层 - Login Log Service（异步版本）
处理登录日志的业务逻辑
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.login_log.model import LoginLog
from core.login_log.schema import LoginLogCreate, LoginLogUpdate


# 状态显示映射
STATUS_DISPLAY = {
    0: "失败",
    1: "成功",
}

# 失败原因显示映射
FAILURE_REASON_DISPLAY = {
    0: "未知错误",
    1: "用户不存在",
    2: "密码错误",
    3: "用户已禁用",
    4: "用户已锁定",
    5: "用户不激活",
    6: "账户异常",
    7: "其他错误",
}


class LoginLogService(BaseService[LoginLog, LoginLogCreate, LoginLogUpdate]):
    """登录日志服务类 - 继承BaseService"""

    model = LoginLog

    # Excel导入导出配置
    excel_columns = {
        "username": "用户名",
        "login_type": "登录方式",
        "status": "登录状态",
        "login_ip": "登录IP",
        "ip_location": "IP属地",
        "browser_type": "浏览器",
        "os_type": "操作系统",
        "device_type": "设备类型",
    }
    excel_sheet_name = "登录日志"

    @staticmethod
    def get_status_display(status: int) -> str:
        """获取状态显示名称"""
        return STATUS_DISPLAY.get(status, "未知")

    @staticmethod
    def get_failure_reason_display(failure_reason: Optional[int]) -> Optional[str]:
        """获取失败原因显示名称"""
        if failure_reason is None:
            return None
        return FAILURE_REASON_DISPLAY.get(failure_reason, "未知")

    @classmethod
    async def record_login(
            cls,
            db: AsyncSession,
            username: str,
            status: int,
            login_ip: str,
            user_id: Optional[str] = None,
            failure_reason: Optional[int] = None,
            failure_message: Optional[str] = None,
            ip_location: Optional[str] = None,
            user_agent: Optional[str] = None,
            browser_type: Optional[str] = None,
            os_type: Optional[str] = None,
            device_type: Optional[str] = None,
            session_id: Optional[str] = None,
            remark: Optional[str] = None,
            login_type: str = "password",
    ) -> LoginLog:
        """记录登录日志"""
        login_log = LoginLog(
            username=username,
            status=status,
            login_ip=login_ip,
            user_id=user_id,
            failure_reason=failure_reason,
            failure_message=failure_message,
            ip_location=ip_location,
            user_agent=user_agent,
            browser_type=browser_type,
            os_type=os_type,
            device_type=device_type,
            session_id=session_id,
            remark=remark,
            login_type=login_type,
        )
        db.add(login_log)
        await db.commit()
        await db.refresh(login_log)
        return login_log

    @classmethod
    async def record_success_login(
            cls,
            db: AsyncSession,
            username: str,
            user_id: Optional[str] = None,
            login_ip: Optional[str] = None,
            ip_location: Optional[str] = None,
            user_agent: Optional[str] = None,
            browser_type: Optional[str] = None,
            os_type: Optional[str] = None,
            device_type: Optional[str] = None,
            session_id: Optional[str] = None,
            remark: Optional[str] = None,
            login_type: str = "password",
    ) -> LoginLog:
        """记录成功登录"""
        return await cls.record_login(
            db=db,
            username=username,
            status=1,
            login_ip=login_ip or "0.0.0.0",
            user_id=user_id,
            ip_location=ip_location,
            user_agent=user_agent,
            browser_type=browser_type,
            os_type=os_type,
            device_type=device_type,
            session_id=session_id,
            remark=remark,
            login_type=login_type,
        )

    @classmethod
    async def record_failed_login(
            cls,
            db: AsyncSession,
            username: str,
            login_ip: str,
            failure_reason: int,
            failure_message: Optional[str] = None,
            ip_location: Optional[str] = None,
            user_agent: Optional[str] = None,
            browser_type: Optional[str] = None,
            os_type: Optional[str] = None,
            device_type: Optional[str] = None,
            remark: Optional[str] = None,
    ) -> LoginLog:
        """记录失败登录"""
        return await cls.record_login(
            db=db,
            username=username,
            status=0,
            login_ip=login_ip,
            failure_reason=failure_reason,
            failure_message=failure_message,
            ip_location=ip_location,
            user_agent=user_agent,
            browser_type=browser_type,
            os_type=os_type,
            device_type=device_type,
        )

    @classmethod
    async def get_user_login_count(
            cls,
            db: AsyncSession,
            user_id: Optional[str] = None,
            username: Optional[str] = None,
            days: int = 30,
    ) -> int:
        """获取用户登录次数（最近N天）"""
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            LoginLog.status == 1,
            LoginLog.sys_create_datetime >= start_date,
        ]

        if user_id:
            conditions.append(LoginLog.user_id == user_id)
        elif username:
            conditions.append(LoginLog.username == username)

        stmt = select(func.count(LoginLog.id)).where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def get_failed_login_count(
            cls,
            db: AsyncSession,
            user_id: Optional[str] = None,
            username: Optional[str] = None,
            days: int = 30,
    ) -> int:
        """获取用户失败登录次数（最近N天）"""
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            LoginLog.status == 0,
            LoginLog.sys_create_datetime >= start_date,
        ]

        if user_id:
            conditions.append(LoginLog.user_id == user_id)
        elif username:
            conditions.append(LoginLog.username == username)

        stmt = select(func.count(LoginLog.id)).where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalar() or 0

    @classmethod
    async def get_last_login(
            cls,
            db: AsyncSession,
            user_id: Optional[str] = None,
            username: Optional[str] = None,
    ) -> Optional[LoginLog]:
        """获取用户最后一次登录记录"""
        conditions = [LoginLog.status == 1]

        if user_id:
            conditions.append(LoginLog.user_id == user_id)
        elif username:
            conditions.append(LoginLog.username == username)

        stmt = select(LoginLog).where(and_(*conditions)).order_by(
            LoginLog.sys_create_datetime.desc()
        ).limit(1)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_login_ips(
            cls,
            db: AsyncSession,
            user_id: Optional[str] = None,
            username: Optional[str] = None,
            days: int = 30,
    ) -> List[str]:
        """获取用户登录过的IP地址列表"""
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            LoginLog.status == 1,
            LoginLog.sys_create_datetime >= start_date,
        ]

        if user_id:
            conditions.append(LoginLog.user_id == user_id)
        elif username:
            conditions.append(LoginLog.username == username)

        stmt = select(LoginLog.login_ip).where(and_(*conditions)).distinct()
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    @classmethod
    async def get_suspicious_logins(
            cls,
            db: AsyncSession,
            max_failed_attempts: int = 5,
            hours: int = 1,
    ) -> List[Dict]:
        """获取可疑登录（短时间内失败次数过多）"""
        start_time = datetime.now() - timedelta(hours=hours)

        stmt = select(
            LoginLog.username,
            LoginLog.login_ip,
            func.count(LoginLog.id).label("count"),
            func.max(LoginLog.sys_create_datetime).label("last_attempt"),
        ).where(
            LoginLog.status == 0,
            LoginLog.sys_create_datetime >= start_time,
        ).group_by(
            LoginLog.username, LoginLog.login_ip
        ).having(
            func.count(LoginLog.id) >= max_failed_attempts
        )

        result = await db.execute(stmt)
        return [
            {
                "username": row.username,
                "login_ip": row.login_ip,
                "count": row.count,
                "last_attempt": row.last_attempt,
            }
            for row in result.fetchall()
        ]

    @classmethod
    async def get_login_stats(
            cls,
            db: AsyncSession,
            days: int = 30,
    ) -> Dict[str, Any]:
        """获取登录统计信息"""
        start_date = datetime.now() - timedelta(days=days)

        base_condition = LoginLog.sys_create_datetime >= start_date

        # 总数
        total_stmt = select(func.count(LoginLog.id)).where(base_condition)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # 成功数
        success_stmt = select(func.count(LoginLog.id)).where(
            base_condition, LoginLog.status == 1
        )
        success_result = await db.execute(success_stmt)
        success = success_result.scalar() or 0

        # 失败数
        failed = total - success

        # 唯一用户数
        unique_users_stmt = select(func.count(func.distinct(LoginLog.user_id))).where(base_condition)
        unique_users_result = await db.execute(unique_users_stmt)
        unique_users = unique_users_result.scalar() or 0

        # 唯一IP数
        unique_ips_stmt = select(func.count(func.distinct(LoginLog.login_ip))).where(base_condition)
        unique_ips_result = await db.execute(unique_ips_stmt)
        unique_ips = unique_ips_result.scalar() or 0

        success_rate = (success / total * 100) if total > 0 else 0

        return {
            "total_logins": total,
            "success_logins": success,
            "failed_logins": failed,
            "success_rate": round(success_rate, 2),
            "unique_users": unique_users,
            "unique_ips": unique_ips,
        }

    @classmethod
    async def get_ip_stats(
            cls,
            db: AsyncSession,
            days: int = 30,
            limit: int = 10,
    ) -> List[Dict]:
        """获取IP登录统计（TOP N）"""
        start_date = datetime.now() - timedelta(days=days)

        stmt = select(
            LoginLog.login_ip,
            LoginLog.ip_location,
            func.count(LoginLog.id).filter(LoginLog.status == 1).label("login_count"),
            func.count(LoginLog.id).filter(LoginLog.status == 0).label("failed_count"),
            func.max(LoginLog.sys_create_datetime).label("last_login_time"),
        ).where(
            LoginLog.sys_create_datetime >= start_date
        ).group_by(
            LoginLog.login_ip, LoginLog.ip_location
        ).order_by(
            func.count(LoginLog.id).filter(LoginLog.status == 1).desc()
        ).limit(limit)

        result = await db.execute(stmt)
        return [
            {
                "login_ip": row.login_ip,
                "ip_location": row.ip_location,
                "login_count": row.login_count or 0,
                "failed_count": row.failed_count or 0,
                "last_login_time": row.last_login_time,
            }
            for row in result.fetchall()
        ]

    @classmethod
    async def get_device_stats(
            cls,
            db: AsyncSession,
            days: int = 30,
    ) -> List[Dict]:
        """获取设备登录统计"""
        start_date = datetime.now() - timedelta(days=days)

        stmt = select(
            LoginLog.device_type,
            LoginLog.browser_type,
            LoginLog.os_type,
            func.count(LoginLog.id).label("login_count"),
            func.max(LoginLog.sys_create_datetime).label("last_login_time"),
        ).where(
            LoginLog.status == 1,
            LoginLog.sys_create_datetime >= start_date,
        ).group_by(
            LoginLog.device_type, LoginLog.browser_type, LoginLog.os_type
        ).order_by(
            func.count(LoginLog.id).desc()
        )

        result = await db.execute(stmt)
        return [
            {
                "device_type": row.device_type,
                "browser_type": row.browser_type,
                "os_type": row.os_type,
                "login_count": row.login_count,
                "last_login_time": row.last_login_time,
            }
            for row in result.fetchall()
        ]

    @classmethod
    async def get_user_stats(
            cls,
            db: AsyncSession,
            days: int = 30,
            limit: int = 10,
    ) -> List[Dict]:
        """获取用户登录统计（TOP N）"""
        start_date = datetime.now() - timedelta(days=days)

        stmt = select(
            LoginLog.user_id,
            LoginLog.username,
            func.count(LoginLog.id).filter(LoginLog.status == 1).label("total_logins"),
            func.count(LoginLog.id).filter(LoginLog.status == 0).label("failed_logins"),
            func.max(LoginLog.sys_create_datetime).filter(LoginLog.status == 1).label("last_login_time"),
            func.max(LoginLog.login_ip).filter(LoginLog.status == 1).label("last_login_ip"),
        ).where(
            LoginLog.sys_create_datetime >= start_date
        ).group_by(
            LoginLog.user_id, LoginLog.username
        ).order_by(
            func.count(LoginLog.id).filter(LoginLog.status == 1).desc()
        ).limit(limit)

        result = await db.execute(stmt)
        return [
            {
                "user_id": row.user_id,
                "username": row.username,
                "total_logins": row.total_logins or 0,
                "failed_logins": row.failed_logins or 0,
                "last_login_time": row.last_login_time,
                "last_login_ip": row.last_login_ip,
            }
            for row in result.fetchall()
        ]

    @classmethod
    async def get_daily_stats(
            cls,
            db: AsyncSession,
            days: int = 30,
    ) -> List[Dict]:
        """获取每日登录统计"""
        start_date = datetime.now() - timedelta(days=days)

        stmt = select(
            func.date(LoginLog.sys_create_datetime).label("date"),
            func.count(LoginLog.id).label("total_logins"),
            func.count(LoginLog.id).filter(LoginLog.status == 1).label("success_logins"),
            func.count(LoginLog.id).filter(LoginLog.status == 0).label("failed_logins"),
            func.count(func.distinct(LoginLog.user_id)).label("unique_users"),
        ).where(
            LoginLog.sys_create_datetime >= start_date
        ).group_by(
            func.date(LoginLog.sys_create_datetime)
        ).order_by(
            func.date(LoginLog.sys_create_datetime)
        )

        result = await db.execute(stmt)
        return [
            {
                "date": str(row.date) if row.date else "",
                "total_logins": row.total_logins,
                "success_logins": row.success_logins or 0,
                "failed_logins": row.failed_logins or 0,
                "unique_users": row.unique_users,
            }
            for row in result.fetchall()
        ]

    @classmethod
    async def clean_old_logs(
            cls,
            db: AsyncSession,
            days: int = 90,
    ) -> int:
        """清理旧的登录日志（默认保留90天）"""
        cutoff_date = datetime.now() - timedelta(days=days)

        stmt = delete(LoginLog).where(LoginLog.sys_create_datetime < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount

    @classmethod
    async def check_user_locked(
            cls,
            db: AsyncSession,
            username: str,
            failed_threshold: int = 5,
            hours: int = 1,
    ) -> bool:
        """检查用户是否应该被锁定（失败次数过多）"""
        start_time = datetime.now() - timedelta(hours=hours)

        stmt = select(func.count(LoginLog.id)).where(
            LoginLog.username == username,
            LoginLog.status == 0,
            LoginLog.sys_create_datetime >= start_time,
        )
        result = await db.execute(stmt)
        failed_count = result.scalar() or 0

        return failed_count >= failed_threshold

    @classmethod
    async def get_logs_by_user(
            cls,
            db: AsyncSession,
            user_id: str,
            days: int = 30,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple:
        """获取指定用户的登录日志"""
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            LoginLog.user_id == user_id,
            LoginLog.sys_create_datetime >= start_date,
        ]

        # 总数
        count_stmt = select(func.count(LoginLog.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 分页数据
        offset = (page - 1) * page_size
        stmt = select(LoginLog).where(and_(*conditions)).order_by(
            LoginLog.sys_create_datetime.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @classmethod
    async def get_logs_by_username(
            cls,
            db: AsyncSession,
            username: str,
            days: int = 30,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple:
        """根据用户名获取登录日志"""
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            LoginLog.username == username,
            LoginLog.sys_create_datetime >= start_date,
        ]

        # 总数
        count_stmt = select(func.count(LoginLog.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 分页数据
        offset = (page - 1) * page_size
        stmt = select(LoginLog).where(and_(*conditions)).order_by(
            LoginLog.sys_create_datetime.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @classmethod
    async def get_logs_by_ip(
            cls,
            db: AsyncSession,
            login_ip: str,
            days: int = 30,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple:
        """根据IP地址获取登录日志"""
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            LoginLog.login_ip == login_ip,
            LoginLog.sys_create_datetime >= start_date,
        ]

        # 总数
        count_stmt = select(func.count(LoginLog.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 分页数据
        offset = (page - 1) * page_size
        stmt = select(LoginLog).where(and_(*conditions)).order_by(
            LoginLog.sys_create_datetime.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total
