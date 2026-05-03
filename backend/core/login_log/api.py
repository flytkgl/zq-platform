#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录日志API - Login Log API（异步版本）
提供登录日志的查询、分析和管理接口
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import PaginatedResponse, ResponseModel
from core.login_log.model import LoginLog
from core.login_log.schema import (
    LoginLogOut,
    LoginLogStatsOut,
    LoginLogIpStatsOut,
    LoginLogDeviceStatsOut,
    LoginLogUserStatsOut,
    LoginLogRecordIn,
    LoginLogDailyStatsOut,
)
from core.login_log.service import LoginLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/login-log", tags=["登录日志"])


# ============ 辅助函数 ============

def _build_log_out(log: LoginLog) -> dict:
    """构建登录日志输出"""
    return {
        "id": str(log.id),
        "user_id": log.user_id,
        "username": log.username,
        "login_type": log.login_type or "password",
        "status": log.status,
        "failure_reason": log.failure_reason,
        "failure_message": log.failure_message,
        "login_ip": log.login_ip,
        "ip_location": log.ip_location,
        "user_agent": log.user_agent,
        "browser_type": log.browser_type,
        "os_type": log.os_type,
        "device_type": log.device_type,
        "duration": log.duration,
        "session_id": log.session_id,
        "remark": log.remark,
        "sys_create_datetime": log.sys_create_datetime,
        "status_display": LoginLogService.get_status_display(log.status),
        "failure_reason_display": LoginLogService.get_failure_reason_display(log.failure_reason),
    }


# ============ 登录日志 CRUD ============

@router.get("", response_model=PaginatedResponse[LoginLogOut], summary="获取登录日志列表")
async def list_login_logs(
        username: Optional[str] = Query(None, description="用户名"),
        user_id: Optional[str] = Query(None, alias="userId", description="用户ID"),
        status: Optional[int] = Query(None, description="登录状态"),
        failure_reason: Optional[int] = Query(None, alias="failureReason", description="失败原因"),
        login_ip: Optional[str] = Query(None, alias="loginIp", description="登录IP"),
        device_type: Optional[str] = Query(None, alias="deviceType", description="设备类型"),
        browser_type: Optional[str] = Query(None, alias="browserType", description="浏览器类型"),
        os_type: Optional[str] = Query(None, alias="osType", description="操作系统"),
        start_datetime: Optional[datetime] = Query(None, alias="startDatetime", description="开始时间"),
        end_datetime: Optional[datetime] = Query(None, alias="endDatetime", description="结束时间"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取登录日志列表（分页）"""
    conditions = []

    if username:
        conditions.append(LoginLog.username.ilike(f"%{username}%"))
    if user_id:
        conditions.append(LoginLog.user_id == user_id)
    if status is not None:
        conditions.append(LoginLog.status == status)
    if failure_reason is not None:
        conditions.append(LoginLog.failure_reason == failure_reason)
    if login_ip:
        conditions.append(LoginLog.login_ip.ilike(f"%{login_ip}%"))
    if device_type:
        conditions.append(LoginLog.device_type == device_type)
    if browser_type:
        conditions.append(LoginLog.browser_type == browser_type)
    if os_type:
        conditions.append(LoginLog.os_type == os_type)
    if start_datetime:
        conditions.append(LoginLog.sys_create_datetime >= start_datetime)
    if end_datetime:
        conditions.append(LoginLog.sys_create_datetime <= end_datetime)

    # 获取总数
    count_stmt = select(func.count(LoginLog.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 获取分页数据
    offset = (page - 1) * page_size
    stmt = select(LoginLog)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(LoginLog.sys_create_datetime.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    items = [_build_log_out(log) for log in result.scalars().all()]

    return PaginatedResponse(items=items, total=total)


@router.get("/{log_id}", response_model=LoginLogOut, summary="获取登录日志详情")
async def get_login_log(
        log_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取单条登录日志的详细信息"""
    log = await LoginLogService.get_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="登录日志不存在")
    return _build_log_out(log)


@router.delete("/{log_id}", response_model=ResponseModel, summary="删除登录日志")
async def delete_login_log(
        log_id: str,
        db: AsyncSession = Depends(get_db),
):
    """删除单条登录日志"""
    success = await LoginLogService.delete(db, log_id, hard=True)
    if not success:
        raise HTTPException(status_code=404, detail="登录日志不存在")
    return ResponseModel(message="登录日志已删除")


@router.delete("/batch/delete", response_model=ResponseModel, summary="批量删除登录日志")
async def batch_delete_login_logs(
        ids: List[str] = Query(..., description="日志ID列表"),
        db: AsyncSession = Depends(get_db),
):
    """批量删除登录日志"""
    success_count, _ = await LoginLogService.batch_delete(db, ids, hard=True)
    return ResponseModel(
        message=f"成功删除 {success_count} 条登录日志",
        data={"deleted_count": success_count}
    )


@router.post("/record", response_model=LoginLogOut, summary="记录登录日志")
async def record_login_log(
        data: LoginLogRecordIn,
        db: AsyncSession = Depends(get_db),
):
    """记录登录日志"""
    log = await LoginLogService.record_login(
        db=db,
        username=data.username,
        status=data.status,
        login_ip=data.login_ip,
        user_id=data.user_id,
        failure_reason=data.failure_reason,
        failure_message=data.failure_message,
        ip_location=data.ip_location,
        user_agent=data.user_agent,
        browser_type=data.browser_type,
        os_type=data.os_type,
        device_type=data.device_type,
        session_id=data.session_id,
        remark=data.remark,
        login_type=data.login_type,
    )
    return _build_log_out(log)


# ============ 统计接口 ============

@router.get("/stats/overview", response_model=LoginLogStatsOut, summary="获取登录统计概览")
async def get_login_stats(
        days: int = Query(30, description="统计天数"),
        db: AsyncSession = Depends(get_db),
):
    """获取登录统计概览"""
    stats = await LoginLogService.get_login_stats(db, days=days)
    return LoginLogStatsOut(**stats)


@router.get("/stats/ip", response_model=List[LoginLogIpStatsOut], summary="获取IP登录统计")
async def get_ip_stats(
        days: int = Query(30, description="统计天数"),
        limit: int = Query(10, description="限制数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取IP登录统计（TOP N）"""
    stats = await LoginLogService.get_ip_stats(db, days=days, limit=limit)
    return [LoginLogIpStatsOut(**item) for item in stats]


@router.get("/stats/device", response_model=List[LoginLogDeviceStatsOut], summary="获取设备登录统计")
async def get_device_stats(
        days: int = Query(30, description="统计天数"),
        db: AsyncSession = Depends(get_db),
):
    """获取设备登录统计"""
    stats = await LoginLogService.get_device_stats(db, days=days)
    return [LoginLogDeviceStatsOut(**item) for item in stats]


@router.get("/stats/user", response_model=List[LoginLogUserStatsOut], summary="获取用户登录统计")
async def get_user_stats(
        days: int = Query(30, description="统计天数"),
        limit: int = Query(10, description="限制数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取用户登录统计（TOP N）"""
    stats = await LoginLogService.get_user_stats(db, days=days, limit=limit)
    return [LoginLogUserStatsOut(**item) for item in stats]


@router.get("/stats/daily", response_model=List[LoginLogDailyStatsOut], summary="获取每日登录统计")
async def get_daily_stats(
        days: int = Query(30, description="统计天数"),
        db: AsyncSession = Depends(get_db),
):
    """获取每日登录统计"""
    stats = await LoginLogService.get_daily_stats(db, days=days)
    return [LoginLogDailyStatsOut(**item) for item in stats]


# ============ 用户相关接口 ============

@router.get("/user/{user_id}", response_model=PaginatedResponse[LoginLogOut], summary="获取用户的登录日志")
async def get_user_login_logs(
        user_id: str,
        days: int = Query(30, description="天数范围"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """获取指定用户的登录日志"""
    items, total = await LoginLogService.get_logs_by_user(
        db, user_id=user_id, days=days, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[_build_log_out(log) for log in items],
        total=total,
    )


@router.get("/user/{user_id}/count", response_model=ResponseModel, summary="获取用户登录次数")
async def get_user_login_count(
        user_id: str,
        days: int = Query(30, description="天数范围"),
        db: AsyncSession = Depends(get_db),
):
    """获取用户登录次数（最近N天）"""
    count = await LoginLogService.get_user_login_count(db, user_id=user_id, days=days)
    failed_count = await LoginLogService.get_failed_login_count(db, user_id=user_id, days=days)
    return ResponseModel(
        message="获取成功",
        data={
            "user_id": user_id,
            "total_logins": count,
            "failed_logins": failed_count,
            "success_logins": count - failed_count,
        }
    )


@router.get("/user/{user_id}/last", response_model=LoginLogOut, summary="获取用户最后一次登录")
async def get_user_last_login(
        user_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取用户最后一次登录记录"""
    log = await LoginLogService.get_last_login(db, user_id=user_id)
    if not log:
        raise HTTPException(status_code=404, detail="未找到用户的登录记录")
    return _build_log_out(log)


@router.get("/user/{user_id}/ips", response_model=ResponseModel, summary="获取用户登录过的IP地址")
async def get_user_login_ips(
        user_id: str,
        days: int = Query(30, description="天数范围"),
        db: AsyncSession = Depends(get_db),
):
    """获取用户最近登录过的IP地址列表"""
    ips = await LoginLogService.get_login_ips(db, user_id=user_id, days=days)
    return ResponseModel(
        message="获取成功",
        data={
            "user_id": user_id,
            "ips": ips,
            "ip_count": len(ips),
        }
    )


# ============ 安全相关接口 ============

@router.get("/suspicious", response_model=ResponseModel, summary="获取可疑登录记录")
async def get_suspicious_logins(
        failed_threshold: int = Query(5, alias="failedThreshold", description="失败次数阈值"),
        hours: int = Query(1, description="小时范围"),
        db: AsyncSession = Depends(get_db),
):
    """获取可疑登录记录"""
    suspicious = await LoginLogService.get_suspicious_logins(
        db, max_failed_attempts=failed_threshold, hours=hours
    )
    return ResponseModel(
        message="获取成功",
        data={
            "suspicious_count": len(suspicious),
            "records": suspicious,
        }
    )


@router.post("/clean", response_model=ResponseModel, summary="清理旧的登录日志")
async def clean_old_logs(
        days: int = Query(90, description="保留天数"),
        db: AsyncSession = Depends(get_db),
):
    """清理旧的登录日志"""
    deleted_count = await LoginLogService.clean_old_logs(db, days=days)
    return ResponseModel(
        message=f"成功清理 {deleted_count} 条旧登录日志",
        data={"deleted_count": deleted_count}
    )


@router.post("/export", response_model=ResponseModel, summary="导出登录日志")
async def export_login_logs():
    """导出登录日志为CSV或Excel"""
    return ResponseModel(message="导出功能待实现")


# ============ 按条件查询接口 ============

@router.get("/username/{username}", response_model=PaginatedResponse[LoginLogOut], summary="根据用户名获取登录日志")
async def get_logs_by_username(
        username: str,
        days: int = Query(30, description="天数范围"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """根据用户名获取登录日志"""
    items, total = await LoginLogService.get_logs_by_username(
        db, username=username, days=days, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[_build_log_out(log) for log in items],
        total=total,
    )


@router.get("/ip/{login_ip}", response_model=PaginatedResponse[LoginLogOut], summary="根据IP地址获取登录日志")
async def get_logs_by_ip(
        login_ip: str,
        days: int = Query(30, description="天数范围"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """根据IP地址获取登录日志"""
    items, total = await LoginLogService.get_logs_by_ip(
        db, login_ip=login_ip, days=days, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[_build_log_out(log) for log in items],
        total=total,
    )


@router.get("/failed-attempts/{username}", response_model=ResponseModel, summary="获取用户登录失败次数")
async def get_failed_attempts(
        username: str,
        hours: int = Query(1, description="小时范围"),
        db: AsyncSession = Depends(get_db),
):
    """获取用户在指定时间内的登录失败次数"""
    start_time = datetime.now() - timedelta(hours=hours)

    stmt = select(func.count(LoginLog.id)).where(
        LoginLog.username == username,
        LoginLog.status == 0,
        LoginLog.sys_create_datetime >= start_time,
    )
    result = await db.execute(stmt)
    failed_count = result.scalar() or 0

    should_lock = await LoginLogService.check_user_locked(
        db, username=username, failed_threshold=5, hours=hours
    )

    return ResponseModel(
        message="获取成功",
        data={
            "username": username,
            "failed_attempts": failed_count,
            "should_lock": should_lock,
        }
    )
