#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler Schema - 定时任务数据验证和序列化
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


# ==================== SchedulerJob Schemas ====================

class SchedulerJobBase(BaseModel):
    """定时任务基础Schema"""
    application_id: Optional[str] = Field(None, description="所属应用ID")
    name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    code: str = Field(..., min_length=1, max_length=128, description="任务编码")
    description: Optional[str] = Field(None, description="任务描述")
    group: str = Field(default="default", max_length=64, description="任务分组")
    trigger_type: str = Field(..., description="触发器类型：cron/interval/date")
    cron_expression: Optional[str] = Field(None, max_length=128, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔时间（秒）")
    run_date: Optional[datetime] = Field(None, description="指定执行时间")
    task_func: str = Field(..., max_length=256, description="任务函数路径")
    task_args: Optional[str] = Field(None, description="任务位置参数（JSON）")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数（JSON）")
    status: int = Field(default=0, description="任务状态：0-禁用，1-启用，2-暂停")
    priority: int = Field(default=0, description="任务优先级")
    max_instances: int = Field(default=1, ge=1, description="最大实例数")
    max_retries: int = Field(default=0, ge=0, description="错误重试次数")
    timeout: Optional[int] = Field(None, ge=1, description="超时时间（秒）")
    coalesce: bool = Field(default=True, description="是否合并执行")
    allow_concurrent: bool = Field(default=False, description="是否允许并发执行")
    remark: Optional[str] = Field(None, description="备注信息")
    sort: int = Field(default=0, description="排序")
    
    @field_validator('trigger_type')
    @classmethod
    def validate_trigger_type(cls, v):
        """验证触发器类型"""
        if v not in ['cron', 'interval', 'date']:
            raise ValueError('触发器类型必须是 cron、interval 或 date')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态"""
        if v not in [0, 1, 2]:
            raise ValueError('状态必须是 0（禁用）、1（启用）或 2（暂停）')
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """验证任务编码格式"""
        if not v:
            raise ValueError('任务编码不能为空')
        if not v.replace('_', '').isalnum():
            raise ValueError('任务编码只能包含字母、数字和下划线')
        return v


class SchedulerJobCreate(SchedulerJobBase):
    """定时任务创建Schema"""
    
    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v, info):
        """验证 Cron 表达式"""
        if info.data.get('trigger_type') == 'cron' and not v:
            raise ValueError('Cron 类型任务必须提供 cron_expression')
        return v
    
    @field_validator('interval_seconds')
    @classmethod
    def validate_interval_seconds(cls, v, info):
        """验证间隔时间"""
        if info.data.get('trigger_type') == 'interval' and not v:
            raise ValueError('Interval 类型任务必须提供 interval_seconds')
        return v
    
    @field_validator('run_date')
    @classmethod
    def validate_run_date(cls, v, info):
        """验证指定时间"""
        if info.data.get('trigger_type') == 'date' and not v:
            raise ValueError('Date 类型任务必须提供 run_date')
        return v


class SchedulerJobUpdate(BaseModel):
    """定时任务更新Schema - 所有字段可选"""
    application_id: Optional[str] = Field(None, description="所属应用ID")
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="任务名称")
    code: Optional[str] = Field(None, min_length=1, max_length=128, description="任务编码")
    description: Optional[str] = Field(None, description="任务描述")
    group: Optional[str] = Field(None, max_length=64, description="任务分组")
    trigger_type: Optional[str] = Field(None, description="触发器类型")
    cron_expression: Optional[str] = Field(None, max_length=128, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔时间（秒）")
    run_date: Optional[datetime] = Field(None, description="指定执行时间")
    task_func: Optional[str] = Field(None, max_length=256, description="任务函数路径")
    task_args: Optional[str] = Field(None, description="任务位置参数（JSON）")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数（JSON）")
    status: Optional[int] = Field(None, description="任务状态")
    priority: Optional[int] = Field(None, description="任务优先级")
    max_instances: Optional[int] = Field(None, ge=1, description="最大实例数")
    max_retries: Optional[int] = Field(None, ge=0, description="错误重试次数")
    timeout: Optional[int] = Field(None, ge=1, description="超时时间（秒）")
    coalesce: Optional[bool] = Field(None, description="是否合并执行")
    allow_concurrent: Optional[bool] = Field(None, description="是否允许并发执行")
    remark: Optional[str] = Field(None, description="备注信息")
    sort: Optional[int] = Field(None, description="排序")


class SchedulerJobResponse(BaseModel):
    """定时任务响应Schema"""
    id: str
    application_id: Optional[str] = None
    name: str
    code: str
    description: Optional[str] = None
    group: str
    trigger_type: str
    trigger_type_display: Optional[str] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    run_date: Optional[CSTDatetime] = None
    task_func: str
    task_args: Optional[str] = None
    task_kwargs: Optional[str] = None
    status: int
    status_display: Optional[str] = None
    priority: int
    max_instances: int
    max_retries: int
    timeout: Optional[int] = None
    coalesce: bool
    allow_concurrent: bool
    total_run_count: int
    success_count: int
    failure_count: int
    success_rate: Optional[float] = None
    last_run_time: Optional[CSTDatetime] = None
    next_run_time: Optional[CSTDatetime] = None
    last_run_status: Optional[str] = None
    last_run_result: Optional[str] = None
    remark: Optional[str] = None
    sort: int = 0
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class SchedulerJobSimple(BaseModel):
    """定时任务简化输出（用于选择器）"""
    id: str
    application_id: Optional[str] = None
    name: str
    code: str
    group: str
    status: int
    
    model_config = ConfigDict(from_attributes=True)


class SchedulerJobBatchDeleteIn(BaseModel):
    """批量删除输入"""
    ids: List[str] = Field(..., description="任务ID列表")


class SchedulerJobBatchDeleteOut(BaseModel):
    """批量删除输出"""
    count: int = Field(..., description="删除成功数量")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class SchedulerJobBatchUpdateStatusIn(BaseModel):
    """批量更新状态输入"""
    ids: List[str] = Field(..., description="任务ID列表")
    status: int = Field(..., description="目标状态：0-禁用，1-启用，2-暂停")


class SchedulerJobBatchUpdateStatusOut(BaseModel):
    """批量更新状态输出"""
    count: int = Field(..., description="更新成功数量")


class SchedulerJobExecuteIn(BaseModel):
    """立即执行任务输入"""
    job_id: str = Field(..., description="任务ID")


class SchedulerJobExecuteOut(BaseModel):
    """立即执行任务输出"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    log_id: Optional[str] = Field(None, description="日志ID")


class SchedulerJobStatisticsOut(BaseModel):
    """任务统计输出"""
    total_jobs: int = Field(..., description="总任务数")
    enabled_jobs: int = Field(..., description="启用任务数")
    disabled_jobs: int = Field(..., description="禁用任务数")
    paused_jobs: int = Field(..., description="暂停任务数")
    total_executions: int = Field(..., description="总执行次数")
    success_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    success_rate: float = Field(..., description="成功率")


class SchedulerJobSearchRequest(BaseModel):
    """搜索任务请求"""
    keyword: str = Field(..., description="搜索关键词")


# ==================== SchedulerLog Schemas ====================

class SchedulerLogResponse(BaseModel):
    """定时任务日志响应Schema"""
    id: str
    job_id: str
    job_name: str
    job_code: str
    status: str
    status_display: Optional[str] = None
    start_time: CSTDatetime
    end_time: Optional[CSTDatetime] = None
    duration: Optional[float] = None
    result: Optional[str] = None
    exception: Optional[str] = None
    traceback: Optional[str] = None
    hostname: Optional[str] = None
    process_id: Optional[int] = None
    retry_count: int
    sys_create_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class SchedulerLogBatchDeleteIn(BaseModel):
    """批量删除日志输入"""
    ids: List[str] = Field(..., description="日志ID列表")


class SchedulerLogBatchDeleteOut(BaseModel):
    """批量删除日志输出"""
    count: int = Field(..., description="删除成功数量")


class SchedulerLogCleanIn(BaseModel):
    """清理日志输入"""
    days: int = Field(..., ge=1, description="保留最近N天的日志")
    status: Optional[str] = Field(None, description="只清理指定状态的日志")


class SchedulerLogCleanOut(BaseModel):
    """清理日志输出"""
    count: int = Field(..., description="清理数量")


# ==================== Scheduler Status Schemas ====================

class SchedulerStatusOut(BaseModel):
    """调度器状态输出"""
    is_running: bool = Field(..., description="是否运行中")
    job_count: int = Field(..., description="任务数量")
    jobs: List[dict] = Field(default=[], description="任务列表")
