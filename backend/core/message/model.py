#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消息模型
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Index, JSON

from app.base_model import BaseModel


class Message(BaseModel):
    """站内消息"""
    __tablename__ = "core_message"

    # 接收人（逻辑外键）
    recipient_id = Column(String(50), nullable=False, index=True, comment="接收人ID")

    # 消息内容
    title = Column(String(200), nullable=False, comment="消息标题")
    content = Column(Text, nullable=False, comment="消息内容")
    msg_type = Column(String(20), default="system", index=True, comment="消息类型: system/workflow/todo/announcement")
    status = Column(String(20), default="unread", index=True, comment="消息状态: unread/read")

    # 关联信息（可选，用于点击跳转）
    link_type = Column(String(50), default="", comment="关联类型")
    link_id = Column(String(50), default="", comment="关联对象ID")

    # 阅读时间
    read_at = Column(DateTime, nullable=True, comment="阅读时间")

    # 发送人（逻辑外键，可选）
    sender_id = Column(String(50), nullable=True, comment="发送人ID")

    __table_args__ = (
        Index("ix_message_recipient_status", "recipient_id", "status"),
        Index("ix_message_recipient_type", "recipient_id", "msg_type"),
    )


class Announcement(BaseModel):
    """公告"""
    __tablename__ = "core_announcement"

    # 公告内容
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容")
    summary = Column(String(500), default="", comment="摘要")

    # 状态与优先级
    status = Column(String(20), default="draft", index=True, comment="状态: draft/published/expired")
    priority = Column(Integer, default=0, index=True, comment="优先级: 0普通/1重要/2紧急")
    is_top = Column(Boolean, default=False, comment="是否置顶")

    # 接收范围
    target_type = Column(String(20), default="all", comment="接收范围类型: all/dept/role/user")
    target_ids = Column(JSON, default=list, comment="接收目标ID列表")

    # 发布时间
    publish_time = Column(DateTime, nullable=True, comment="发布时间")
    expire_time = Column(DateTime, nullable=True, comment="过期时间")

    # 发布人（逻辑外键）
    publisher_id = Column(String(50), nullable=True, comment="发布人ID")

    # 统计
    read_count = Column(Integer, default=0, comment="阅读次数")


class AnnouncementRead(BaseModel):
    """公告阅读记录"""
    __tablename__ = "core_announcement_read"

    # 公告（逻辑外键）
    announcement_id = Column(String(50), nullable=False, index=True, comment="公告ID")

    # 用户（逻辑外键）
    user_id = Column(String(50), nullable=False, index=True, comment="用户ID")

    # 阅读时间
    read_at = Column(DateTime, nullable=True, comment="阅读时间")

    __table_args__ = (
        Index("ix_announcement_read_unique", "announcement_id", "user_id", unique=True),
    )
