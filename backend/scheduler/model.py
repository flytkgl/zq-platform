#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler Model - 定时任务模型
用于管理定时任务和执行记录
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, Float, Index

from app.base_model import BaseModel


class SchedulerJob(BaseModel):
    """
    定时任务模型 - 用于管理定时任务配置
    
    功能特点：
    1. 支持多种触发器类型（cron、interval、date）
    2. 支持任务启用/禁用
    3. 支持任务分组管理
    4. 支持任务优先级
    5. 记录任务执行统计信息
    6. 支持任务参数配置
    """
    __tablename__ = "core_scheduler_job"
    
    # 所属应用（逻辑外键关联 core_application）
    application_id = Column(String(21), nullable=True, index=True, comment="所属应用ID")
    
    # 任务类型选择
    TRIGGER_TYPE_CHOICES = {
        'cron': 'Cron表达式',
        'interval': '间隔执行',
        'date': '指定时间',
    }
    
    # 任务状态选择
    STATUS_CHOICES = {
        0: '禁用',
        1: '启用',
        2: '暂停',
    }
    
    # 任务名称
    name = Column(String(128), nullable=False, index=True, comment="任务名称")
    
    # 任务编码（唯一标识）
    code = Column(String(128), unique=True, nullable=False, index=True, comment="任务编码")
    
    # 任务描述
    description = Column(Text, nullable=True, comment="任务描述")
    
    # 任务分组
    group = Column(String(64), default='default', index=True, comment="任务分组")
    
    # 触发器类型
    trigger_type = Column(String(20), default='cron', index=True, comment="触发器类型")
    
    # Cron 表达式（用于 cron 类型）
    cron_expression = Column(String(128), nullable=True, comment="Cron表达式")
    
    # 间隔时间（秒，用于 interval 类型）
    interval_seconds = Column(Integer, nullable=True, comment="间隔时间（秒）")
    
    # 指定执行时间（用于 date 类型）
    run_date = Column(DateTime, nullable=True, comment="指定执行时间")
    
    # 任务函数路径（如：scheduler.tasks.test_task）
    task_func = Column(String(256), nullable=False, comment="任务函数路径")
    
    # 任务参数（JSON格式）
    task_args = Column(Text, nullable=True, comment="任务位置参数（JSON数组格式）")
    
    # 任务关键字参数（JSON格式）
    task_kwargs = Column(Text, nullable=True, comment="任务关键字参数（JSON对象格式）")
    
    # 任务状态
    status = Column(Integer, default=0, index=True, comment="任务状态（0-禁用，1-启用，2-暂停）")
    
    # 任务优先级（数字越大优先级越高）
    priority = Column(Integer, default=0, index=True, comment="任务优先级")
    
    # 最大实例数（同时运行的任务实例数）
    max_instances = Column(Integer, default=1, comment="最大实例数")
    
    # 错误重试次数
    max_retries = Column(Integer, default=0, comment="错误重试次数")
    
    # 超时时间（秒）
    timeout = Column(Integer, nullable=True, comment="超时时间（秒）")
    
    # 是否合并执行（如果上次未执行完，是否跳过本次）
    coalesce = Column(Boolean, default=True, comment="是否合并执行")
    
    # 是否允许并发执行
    allow_concurrent = Column(Boolean, default=False, comment="是否允许并发执行")
    
    # 执行统计
    total_run_count = Column(Integer, default=0, comment="总执行次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    failure_count = Column(Integer, default=0, comment="失败次数")
    
    # 最后执行时间
    last_run_time = Column(DateTime, nullable=True, comment="最后执行时间")
    
    # 下次执行时间
    next_run_time = Column(DateTime, nullable=True, comment="下次执行时间")
    
    # 最后执行状态
    last_run_status = Column(String(20), nullable=True, comment="最后执行状态")
    
    # 最后执行结果
    last_run_result = Column(Text, nullable=True, comment="最后执行结果")
    
    # 备注
    remark = Column(Text, nullable=True, comment="备注信息")
    
    # 复合索引
    __table_args__ = (
        Index('ix_scheduler_job_status_trigger', 'status', 'trigger_type'),
        Index('ix_scheduler_job_group_status', 'group', 'status'),
        Index('ix_scheduler_job_priority_status', 'priority', 'status'),
        Index('ix_scheduler_job_next_run_status', 'next_run_time', 'status'),
    )
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def is_enabled(self) -> bool:
        """判断任务是否启用"""
        return self.status == 1
    
    def is_paused(self) -> bool:
        """判断任务是否暂停"""
        return self.status == 2
    
    def is_disabled(self) -> bool:
        """判断任务是否禁用"""
        return self.status == 0
    
    def get_status_display(self) -> str:
        """获取状态的显示名称"""
        return self.STATUS_CHOICES.get(self.status, '未知')
    
    def get_trigger_type_display(self) -> str:
        """获取触发器类型的显示名称"""
        return self.TRIGGER_TYPE_CHOICES.get(self.trigger_type, '未知')
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_run_count == 0:
            return 0.0
        return round(self.success_count / self.total_run_count * 100, 2)


class SchedulerLog(BaseModel):
    """
    定时任务执行日志模型
    
    功能特点：
    1. 记录每次任务执行的详细信息
    2. 记录执行时间、状态、结果
    3. 记录异常信息
    4. 支持日志查询和统计
    """
    __tablename__ = "core_scheduler_log"
    
    # 执行状态选择
    STATUS_CHOICES = {
        'pending': '等待执行',
        'running': '执行中',
        'success': '执行成功',
        'failed': '执行失败',
        'timeout': '执行超时',
        'skipped': '跳过执行',
    }
    
    # 关联的任务ID（逻辑外键）
    job_id = Column(String(36), nullable=False, index=True, comment="任务ID")
    
    # 任务名称（冗余字段，便于查询）
    job_name = Column(String(128), nullable=False, index=True, comment="任务名称")
    
    # 任务编码（冗余字段，便于查询）
    job_code = Column(String(128), nullable=False, index=True, comment="任务编码")
    
    # 执行状态
    status = Column(String(20), default='pending', index=True, comment="执行状态")
    
    # 开始时间
    start_time = Column(DateTime, nullable=False, index=True, comment="开始时间")
    
    # 结束时间
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    
    # 执行耗时（秒）
    duration = Column(Float, nullable=True, comment="执行耗时（秒）")
    
    # 执行结果
    result = Column(Text, nullable=True, comment="执行结果")
    
    # 异常信息
    exception = Column(Text, nullable=True, comment="异常信息")
    
    # 异常堆栈
    traceback = Column(Text, nullable=True, comment="异常堆栈")
    
    # 执行主机
    hostname = Column(String(128), nullable=True, comment="执行主机")
    
    # 进程ID
    process_id = Column(Integer, nullable=True, comment="进程ID")
    
    # 重试次数
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    # 复合索引
    __table_args__ = (
        Index('ix_scheduler_log_job_status', 'job_id', 'status'),
        Index('ix_scheduler_log_status_start', 'status', 'start_time'),
        Index('ix_scheduler_log_code_start', 'job_code', 'start_time'),
    )
    
    def __str__(self):
        return f"{self.job_name} - {self.status} - {self.start_time}"
    
    def is_success(self) -> bool:
        """判断是否执行成功"""
        return self.status == 'success'
    
    def is_failed(self) -> bool:
        """判断是否执行失败"""
        return self.status == 'failed'
    
    def is_running(self) -> bool:
        """判断是否正在执行"""
        return self.status == 'running'
    
    def get_status_display(self) -> str:
        """获取状态的显示名称"""
        return self.STATUS_CHOICES.get(self.status, '未知')
