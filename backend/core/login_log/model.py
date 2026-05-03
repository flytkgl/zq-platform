#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录日志模型 - Login Log Model
记录用户的所有登录操作，包括成功和失败的尝试
"""
from sqlalchemy import Column, String, Text, Integer, Index

from app.base_model import BaseModel


class LoginLog(BaseModel):
    """
    登录日志模型 - 完整记录用户登录信息
    """
    __tablename__ = "core_login_log"

    # 用户ID
    user_id = Column(String(36), nullable=True, index=True, comment="用户ID")

    # 用户名
    username = Column(String(150), nullable=False, index=True, comment="用户名")

    # 登录方式
    login_type = Column(String(20), default="password", index=True, comment="登录方式")

    # 登录状态：0-失败，1-成功
    status = Column(Integer, default=0, index=True, comment="登录状态")

    # 失败原因（仅当status=0时有效）
    failure_reason = Column(Integer, nullable=True, comment="登录失败原因")

    # 失败详细信息
    failure_message = Column(String(255), nullable=True, comment="登录失败详细信息")

    # 登录IP地址
    login_ip = Column(String(50), nullable=False, index=True, comment="登录IP地址")

    # IP属地（地区信息，可选）
    ip_location = Column(String(100), nullable=True, comment="IP属地")

    # 用户代理（浏览器信息）
    user_agent = Column(Text, nullable=True, comment="用户代理字符串")

    # 浏览器类型
    browser_type = Column(String(50), nullable=True, comment="浏览器类型")

    # 操作系统
    os_type = Column(String(50), nullable=True, comment="操作系统类型")

    # 设备类型（桌面、移动、平板等）
    device_type = Column(String(20), nullable=True, comment="设备类型")

    # 登录时长（从登录到退出，单位：秒）
    duration = Column(Integer, nullable=True, default=0, comment="登录会话时长（秒）")

    # 会话ID
    session_id = Column(String(128), nullable=True, unique=True, comment="会话ID")

    # 备注
    remark = Column(String(255), nullable=True, comment="备注信息")

    __table_args__ = (
        Index("ix_login_log_user_datetime", "user_id", "sys_create_datetime"),
        Index("ix_login_log_username_status", "username", "status"),
        Index("ix_login_log_status_datetime", "status", "sys_create_datetime"),
        Index("ix_login_log_ip_datetime", "login_ip", "sys_create_datetime"),
        Index("ix_login_log_type_datetime", "login_type", "sys_create_datetime"),
        Index("ix_login_log_user_type", "user_id", "login_type"),
    )
