#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FeishuSyncLog Model - 飞书同步日志模型
记录每次组织架构/用户同步的执行情况
"""
from sqlalchemy import Column, String, Text, Integer, DateTime

from app.base_model import BaseModel


class FeishuSyncLog(BaseModel):
    """
    飞书同步日志

    字段说明：
    - sync_type: 同步类型 dept=部门 user=用户
    - total_count: 飞书侧总数
    - success_count: 同步成功数
    - fail_count: 同步失败数
    - status: 同步状态 running/success/partial/failed
    - error_detail: 失败详情（JSON）
    - started_at: 同步开始时间
    - finished_at: 同步结束时间
    """
    __tablename__ = "core_feishu_sync_log"

    sync_type = Column(String(20), nullable=False, index=True, comment="同步类型: dept/user")
    total_count = Column(Integer, default=0, comment="总数")
    success_count = Column(Integer, default=0, comment="成功数")
    fail_count = Column(Integer, default=0, comment="失败数")
    status = Column(String(20), default="running", index=True, comment="状态: running/success/partial/failed")
    error_detail = Column(Text, nullable=True, comment="失败详情")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="结束时间")

    def __repr__(self):
        return f"<FeishuSyncLog {self.sync_type} {self.status}>"
