#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录日志数据验证模式 - Login Log Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.base_schema import CSTDatetime


class LoginLogCreate(BaseModel):
    """登录日志创建"""
    username: str = Field(..., description="用户名")
    user_id: Optional[str] = Field(None, description="用户ID")
    status: int = Field(..., description="登录状态：0-失败，1-成功")
    failure_reason: Optional[int] = Field(None, description="失败原因")
    failure_message: Optional[str] = Field(None, description="失败信息")
    login_ip: str = Field(..., description="登录IP")
    ip_location: Optional[str] = Field(None, description="IP属地")
    user_agent: Optional[str] = Field(None, description="用户代理")
    browser_type: Optional[str] = Field(None, description="浏览器类型")
    os_type: Optional[str] = Field(None, description="操作系统")
    device_type: Optional[str] = Field(None, description="设备类型")
    session_id: Optional[str] = Field(None, description="会话ID")
    remark: Optional[str] = Field(None, description="备注")
    login_type: str = Field(default="password", description="登录方式")


class LoginLogUpdate(BaseModel):
    """登录日志更新（一般不更新）"""
    remark: Optional[str] = Field(None, description="备注")
    duration: Optional[int] = Field(None, description="登录时长")


class LoginLogOut(BaseModel):
    """登录日志输出"""
    id: str
    user_id: Optional[str] = None
    username: str
    login_type: str
    status: int
    failure_reason: Optional[int] = None
    failure_message: Optional[str] = None
    login_ip: str
    ip_location: Optional[str] = None
    user_agent: Optional[str] = None
    browser_type: Optional[str] = None
    os_type: Optional[str] = None
    device_type: Optional[str] = None
    duration: Optional[int] = None
    session_id: Optional[str] = None
    remark: Optional[str] = None
    sys_create_datetime: CSTDatetime

    # 显示字段
    status_display: Optional[str] = None
    failure_reason_display: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoginLogRecordIn(BaseModel):
    """记录登录日志输入"""
    username: str = Field(..., description="用户名")
    user_id: Optional[str] = Field(None, description="用户ID")
    status: int = Field(..., description="登录状态：0-失败，1-成功")
    failure_reason: Optional[int] = Field(None, description="失败原因")
    failure_message: Optional[str] = Field(None, description="失败信息")
    login_ip: str = Field(..., description="登录IP")
    ip_location: Optional[str] = Field(None, description="IP属地")
    user_agent: Optional[str] = Field(None, description="用户代理")
    browser_type: Optional[str] = Field(None, description="浏览器类型")
    os_type: Optional[str] = Field(None, description="操作系统")
    device_type: Optional[str] = Field(None, description="设备类型")
    session_id: Optional[str] = Field(None, description="会话ID")
    remark: Optional[str] = Field(None, description="备注")
    login_type: str = Field(default="password", description="登录方式")


class LoginLogStatsOut(BaseModel):
    """登录统计输出"""
    total_logins: int = Field(..., description="总登录次数")
    success_logins: int = Field(..., description="成功登录次数")
    failed_logins: int = Field(..., description="失败登录次数")
    success_rate: float = Field(..., description="成功率（%）")
    unique_users: int = Field(..., description="登录用户数")
    unique_ips: int = Field(..., description="登录IP数")


class LoginLogIpStatsOut(BaseModel):
    """IP登录统计"""
    login_ip: str = Field(..., description="IP地址")
    ip_location: Optional[str] = Field(None, description="IP属地")
    login_count: int = Field(..., description="登录次数")
    failed_count: int = Field(..., description="失败次数")
    last_login_time: Optional[CSTDatetime] = Field(None, description="最后登录时间")


class LoginLogDeviceStatsOut(BaseModel):
    """设备登录统计"""
    device_type: Optional[str] = Field(None, description="设备类型")
    browser_type: Optional[str] = Field(None, description="浏览器类型")
    os_type: Optional[str] = Field(None, description="操作系统")
    login_count: int = Field(..., description="登录次数")
    last_login_time: Optional[CSTDatetime] = Field(None, description="最后登录时间")


class LoginLogUserStatsOut(BaseModel):
    """用户登录统计"""
    user_id: Optional[str] = Field(None, description="用户ID")
    username: str = Field(..., description="用户名")
    total_logins: int = Field(..., description="登录次数")
    failed_logins: int = Field(..., description="失败次数")
    last_login_time: Optional[CSTDatetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")


class LoginLogDailyStatsOut(BaseModel):
    """每日登录统计"""
    date: str = Field(..., description="日期")
    total_logins: int = Field(..., description="登录总数")
    success_logins: int = Field(..., description="成功登录数")
    failed_logins: int = Field(..., description="失败登录数")
    unique_users: int = Field(..., description="登录用户数")
