#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler API - 定时任务管理接口
提供定时任务的 CRUD 操作和管理功能
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from scheduler.model import SchedulerJob, SchedulerLog
from scheduler.schema import (
    SchedulerJobCreate,
    SchedulerJobUpdate,
    SchedulerJobResponse,
    SchedulerJobSimple,
    SchedulerJobBatchDeleteIn,
    SchedulerJobBatchDeleteOut,
    SchedulerJobBatchUpdateStatusIn,
    SchedulerJobBatchUpdateStatusOut,
    SchedulerJobExecuteIn,
    SchedulerJobExecuteOut,
    SchedulerJobStatisticsOut,
    SchedulerJobSearchRequest,
    SchedulerLogResponse,
    SchedulerLogBatchDeleteIn,
    SchedulerLogBatchDeleteOut,
    SchedulerLogCleanIn,
    SchedulerLogCleanOut,
    SchedulerStatusOut,
)
from scheduler.service import scheduler_service

router = APIRouter(prefix="/scheduler", tags=["定时任务管理"])


def _build_job_response(job: SchedulerJob) -> SchedulerJobResponse:
    """构建任务响应"""
    return SchedulerJobResponse(
        id=job.id,
        application_id=job.application_id,
        name=job.name,
        code=job.code,
        description=job.description,
        group=job.group,
        trigger_type=job.trigger_type,
        trigger_type_display=job.get_trigger_type_display(),
        cron_expression=job.cron_expression,
        interval_seconds=job.interval_seconds,
        run_date=job.run_date,
        task_func=job.task_func,
        task_args=job.task_args,
        task_kwargs=job.task_kwargs,
        status=job.status,
        status_display=job.get_status_display(),
        priority=job.priority,
        max_instances=job.max_instances,
        max_retries=job.max_retries,
        timeout=job.timeout,
        coalesce=job.coalesce,
        allow_concurrent=job.allow_concurrent,
        total_run_count=job.total_run_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        success_rate=job.get_success_rate(),
        last_run_time=job.last_run_time,
        next_run_time=job.next_run_time,
        last_run_status=job.last_run_status,
        last_run_result=job.last_run_result,
        remark=job.remark,
        sort=job.sort,
        sys_create_datetime=job.sys_create_datetime,
        sys_update_datetime=job.sys_update_datetime,
    )


def _build_log_response(log: SchedulerLog) -> SchedulerLogResponse:
    """构建日志响应"""
    return SchedulerLogResponse(
        id=log.id,
        job_id=log.job_id,
        job_name=log.job_name,
        job_code=log.job_code,
        status=log.status,
        status_display=log.get_status_display(),
        start_time=log.start_time,
        end_time=log.end_time,
        duration=log.duration,
        result=log.result,
        exception=log.exception,
        traceback=log.traceback,
        hostname=log.hostname,
        process_id=log.process_id,
        retry_count=log.retry_count,
        sys_create_datetime=log.sys_create_datetime,
    )


# ==================== SchedulerJob APIs ====================

@router.post("/job", response_model=SchedulerJobResponse, summary="创建定时任务")
async def create_scheduler_job(data: SchedulerJobCreate, db: AsyncSession = Depends(get_db)):
    """创建新的定时任务"""
    # 检查任务编码是否已存在
    result = await db.execute(
        select(SchedulerJob).where(
            SchedulerJob.code == data.code,
            SchedulerJob.is_deleted == False  # noqa: E712
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"任务编码已存在: {data.code}")

    # 创建任务
    job = SchedulerJob(**data.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 如果任务是启用状态，添加到调度器
    if job.is_enabled() and scheduler_service.is_running():
        await scheduler_service.add_job(job)

    return _build_job_response(job)


@router.get("/job/all", response_model=List[SchedulerJobSimple], summary="获取所有定时任务（简化版）")
async def get_all_scheduler_jobs(
    application_id: str = Query(None, alias="applicationId", description="所属应用ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有定时任务（不分页，简化版）"""
    conditions = [SchedulerJob.is_deleted == False]  # noqa: E712
    if application_id:
        conditions.append(SchedulerJob.application_id == application_id)
    else:
        conditions.append(SchedulerJob.application_id.is_(None))
    
    result = await db.execute(
        select(SchedulerJob).where(*conditions).order_by(SchedulerJob.priority.desc(), SchedulerJob.name)
    )
    jobs = result.scalars().all()
    return jobs


@router.get("/job", response_model=PaginatedResponse[SchedulerJobResponse], summary="获取定时任务列表")
async def get_scheduler_job_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    application_id: str = Query(None, alias="applicationId", description="所属应用ID"),
    name: Optional[str] = Query(default=None, description="任务名称"),
    code: Optional[str] = Query(default=None, description="任务编码"),
    group: Optional[str] = Query(default=None, description="任务分组"),
    trigger_type: Optional[str] = Query(default=None, description="触发器类型"),
    status: Optional[int] = Query(default=None, description="任务状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取定时任务列表（分页）"""
    filters = [SchedulerJob.is_deleted == False]  # noqa: E712
    # 应用过滤
    if application_id:
        filters.append(SchedulerJob.application_id == application_id)
    else:
        filters.append(SchedulerJob.application_id.is_(None))
    if name:
        filters.append(SchedulerJob.name.ilike(f"%{name}%"))
    if code:
        filters.append(SchedulerJob.code.ilike(f"%{code}%"))
    if group:
        filters.append(SchedulerJob.group == group)
    if trigger_type:
        filters.append(SchedulerJob.trigger_type == trigger_type)
    if status is not None:
        filters.append(SchedulerJob.status == status)

    # 查询总数
    count_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(*filters)
    )
    total = count_result.scalar()

    # 查询数据
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SchedulerJob).where(*filters)
        .order_by(SchedulerJob.priority.desc(), SchedulerJob.sys_update_datetime.desc())
        .offset(offset).limit(page_size)
    )
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=[_build_job_response(job) for job in jobs],
        total=total
    )


@router.post("/job/batch/delete", response_model=SchedulerJobBatchDeleteOut, summary="批量删除定时任务")
async def batch_delete_scheduler_jobs(
    data: SchedulerJobBatchDeleteIn,
    db: AsyncSession = Depends(get_db)
):
    """批量删除定时任务"""
    success_count = 0
    failed_ids = []

    for job_id in data.ids:
        try:
            result = await db.execute(
                select(SchedulerJob).where(SchedulerJob.id == job_id)
            )
            job = result.scalar_one_or_none()

            if job:
                # 从调度器移除
                if scheduler_service.is_running():
                    await scheduler_service.remove_job(job.code)

                # 软删除
                job.is_deleted = True
                success_count += 1
            else:
                failed_ids.append(job_id)
        except Exception:
            failed_ids.append(job_id)

    await db.commit()
    return SchedulerJobBatchDeleteOut(count=success_count, failed_ids=failed_ids)


@router.post("/job/batch/update_status", response_model=SchedulerJobBatchUpdateStatusOut, summary="批量更新任务状态")
async def batch_update_scheduler_job_status(
    data: SchedulerJobBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量启用、禁用或暂停任务"""
    result = await db.execute(
        select(SchedulerJob).where(SchedulerJob.id.in_(data.ids))
    )
    jobs = result.scalars().all()

    count = 0
    for job in jobs:
        job.status = data.status
        count += 1

        # 同步更新调度器
        if scheduler_service.is_running():
            if job.is_enabled():
                await scheduler_service.add_job(job)
            elif job.is_paused():
                await scheduler_service.pause_job(job.code)
            else:
                await scheduler_service.remove_job(job.code)

    await db.commit()
    return SchedulerJobBatchUpdateStatusOut(count=count)


@router.post("/job/execute", response_model=SchedulerJobExecuteOut, summary="立即执行任务")
async def execute_scheduler_job(
    data: SchedulerJobExecuteIn,
    db: AsyncSession = Depends(get_db)
):
    """立即执行指定任务（不影响正常调度）"""
    result = await db.execute(
        select(SchedulerJob).where(SchedulerJob.id == data.job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not scheduler_service.is_running():
        raise HTTPException(status_code=400, detail="调度器未运行")

    # 立即执行任务
    success = await scheduler_service.run_job_now(job.code)

    if success:
        return SchedulerJobExecuteOut(
            success=True,
            message=f"任务 {job.name} 将立即执行"
        )
    else:
        return SchedulerJobExecuteOut(
            success=False,
            message=f"任务 {job.name} 执行失败，可能任务未在调度器中"
        )


@router.post("/job/search", response_model=PaginatedResponse[SchedulerJobResponse], summary="搜索定时任务")
async def search_scheduler_jobs(
    data: SchedulerJobSearchRequest,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """搜索定时任务"""
    keyword = data.keyword
    filters = [
        SchedulerJob.is_deleted == False,  # noqa: E712
        or_(
            SchedulerJob.name.ilike(f"%{keyword}%"),
            SchedulerJob.code.ilike(f"%{keyword}%"),
            SchedulerJob.description.ilike(f"%{keyword}%"),
        )
    ]

    # 查询总数
    count_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(*filters)
    )
    total = count_result.scalar()

    # 查询数据
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SchedulerJob).where(*filters)
        .order_by(SchedulerJob.priority.desc())
        .offset(offset).limit(page_size)
    )
    jobs = result.scalars().all()

    return PaginatedResponse(
        items=[_build_job_response(job) for job in jobs],
        total=total
    )


@router.get("/job/statistics/data", response_model=SchedulerJobStatisticsOut, summary="获取任务统计信息")
async def get_scheduler_job_statistics(db: AsyncSession = Depends(get_db)):
    """获取任务统计信息"""
    # 任务统计
    total_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(SchedulerJob.is_deleted == False)  # noqa: E712
    )
    total_jobs = total_result.scalar() or 0

    enabled_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted == False,  # noqa: E712
            SchedulerJob.status == 1
        )
    )
    enabled_jobs = enabled_result.scalar() or 0

    disabled_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted == False,  # noqa: E712
            SchedulerJob.status == 0
        )
    )
    disabled_jobs = disabled_result.scalar() or 0

    paused_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted == False,  # noqa: E712
            SchedulerJob.status == 2
        )
    )
    paused_jobs = paused_result.scalar() or 0

    # 执行统计
    total_exec_result = await db.execute(
        select(func.count(SchedulerLog.id))
    )
    total_executions = total_exec_result.scalar() or 0

    success_exec_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(SchedulerLog.status == 'success')
    )
    success_executions = success_exec_result.scalar() or 0

    failed_exec_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(SchedulerLog.status == 'failed')
    )
    failed_executions = failed_exec_result.scalar() or 0

    # 计算成功率
    success_rate = round(success_executions / total_executions * 100, 2) if total_executions > 0 else 0

    return SchedulerJobStatisticsOut(
        total_jobs=total_jobs,
        enabled_jobs=enabled_jobs,
        disabled_jobs=disabled_jobs,
        paused_jobs=paused_jobs,
        total_executions=total_executions,
        success_executions=success_executions,
        failed_executions=failed_executions,
        success_rate=success_rate,
    )


@router.get("/job/{job_id}", response_model=SchedulerJobResponse, summary="获取定时任务详情")
async def get_scheduler_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个定时任务的详细信息"""
    result = await db.execute(
        select(SchedulerJob).where(SchedulerJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    return _build_job_response(job)


@router.put("/job/{job_id}", response_model=SchedulerJobResponse, summary="更新定时任务")
async def update_scheduler_job(
    job_id: str,
    data: SchedulerJobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新定时任务"""
    result = await db.execute(
        select(SchedulerJob).where(SchedulerJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查任务编码是否已存在（排除自身）
    if data.code:
        code_result = await db.execute(
            select(SchedulerJob).where(
                SchedulerJob.code == data.code,
                SchedulerJob.id != job_id,
                SchedulerJob.is_deleted == False  # noqa: E712
            )
        )
        if code_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"任务编码已存在: {data.code}")

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job, key, value)

    await db.commit()
    await db.refresh(job)

    # 同步更新调度器
    if scheduler_service.is_running():
        await scheduler_service.modify_job(job)

    return _build_job_response(job)


@router.delete("/job/{job_id}", response_model=ResponseModel, summary="删除定时任务")
async def delete_scheduler_job(
    job_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除定时任务"""
    result = await db.execute(
        select(SchedulerJob).where(SchedulerJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 从调度器移除
    if scheduler_service.is_running():
        await scheduler_service.remove_job(job.code)

    if hard:
        await db.delete(job)
    else:
        job.is_deleted = True

    await db.commit()
    return ResponseModel(message="删除成功")


# ==================== SchedulerLog APIs ====================

@router.get("/log", response_model=PaginatedResponse[SchedulerLogResponse], summary="获取任务执行日志列表")
async def get_scheduler_log_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    job_id: Optional[str] = Query(default=None, description="任务ID"),
    job_code: Optional[str] = Query(default=None, description="任务编码"),
    job_name: Optional[str] = Query(default=None, description="任务名称"),
    status: Optional[str] = Query(default=None, description="执行状态"),
    start_time_gte: Optional[datetime] = Query(default=None, alias="startTimeGte", description="开始时间>="),
    start_time_lte: Optional[datetime] = Query(default=None, alias="startTimeLte", description="开始时间<="),
    db: AsyncSession = Depends(get_db)
):
    """获取任务执行日志列表（分页）"""
    filters = []
    if job_id:
        filters.append(SchedulerLog.job_id == job_id)
    if job_code:
        filters.append(SchedulerLog.job_code.ilike(f"%{job_code}%"))
    if job_name:
        filters.append(SchedulerLog.job_name.ilike(f"%{job_name}%"))
    if status:
        filters.append(SchedulerLog.status == status)
    if start_time_gte:
        filters.append(SchedulerLog.start_time >= start_time_gte)
    if start_time_lte:
        filters.append(SchedulerLog.start_time <= start_time_lte)

    # 查询总数
    count_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(*filters) if filters else select(func.count(SchedulerLog.id))
    )
    total = count_result.scalar()

    # 查询数据
    offset = (page - 1) * page_size
    query = select(SchedulerLog).order_by(SchedulerLog.start_time.desc()).offset(offset).limit(page_size)
    if filters:
        query = select(SchedulerLog).where(*filters).order_by(SchedulerLog.start_time.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[_build_log_response(log) for log in logs],
        total=total
    )


@router.get("/log/by/job/{job_id}", response_model=PaginatedResponse[SchedulerLogResponse], summary="获取指定任务的执行日志")
async def get_scheduler_logs_by_job(
    job_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定任务的所有执行日志"""
    # 查询总数
    count_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(SchedulerLog.job_id == job_id)
    )
    total = count_result.scalar()

    # 查询数据
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SchedulerLog).where(SchedulerLog.job_id == job_id)
        .order_by(SchedulerLog.start_time.desc())
        .offset(offset).limit(page_size)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[_build_log_response(log) for log in logs],
        total=total
    )


@router.get("/log/{log_id}", response_model=SchedulerLogResponse, summary="获取任务执行日志详情")
async def get_scheduler_log(log_id: str, db: AsyncSession = Depends(get_db)):
    """获取单个任务执行日志的详细信息"""
    result = await db.execute(
        select(SchedulerLog).where(SchedulerLog.id == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    return _build_log_response(log)


@router.delete("/log/{log_id}", response_model=ResponseModel, summary="删除任务执行日志")
async def delete_scheduler_log(log_id: str, db: AsyncSession = Depends(get_db)):
    """删除任务执行日志"""
    result = await db.execute(
        select(SchedulerLog).where(SchedulerLog.id == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    await db.delete(log)
    await db.commit()
    return ResponseModel(message="删除成功")


@router.post("/log/batch/delete", response_model=SchedulerLogBatchDeleteOut, summary="批量删除任务执行日志")
async def batch_delete_scheduler_logs(
    data: SchedulerLogBatchDeleteIn,
    db: AsyncSession = Depends(get_db)
):
    """批量删除任务执行日志"""
    result = await db.execute(
        select(SchedulerLog).where(SchedulerLog.id.in_(data.ids))
    )
    logs = result.scalars().all()

    count = len(logs)
    for log in logs:
        await db.delete(log)

    await db.commit()
    return SchedulerLogBatchDeleteOut(count=count)


@router.post("/log/clean", response_model=SchedulerLogCleanOut, summary="清理旧日志")
async def clean_scheduler_logs(
    data: SchedulerLogCleanIn,
    db: AsyncSession = Depends(get_db)
):
    """清理旧日志"""
    cutoff_date = datetime.now() - timedelta(days=data.days)

    filters = [SchedulerLog.start_time < cutoff_date]
    if data.status:
        filters.append(SchedulerLog.status == data.status)

    result = await db.execute(
        select(SchedulerLog).where(*filters)
    )
    logs = result.scalars().all()

    count = len(logs)
    for log in logs:
        await db.delete(log)

    await db.commit()
    return SchedulerLogCleanOut(count=count)


# ==================== Scheduler Control APIs ====================

@router.post("/start", response_model=ResponseModel, summary="启动调度器")
async def start_scheduler():
    """启动调度器（注意：调度器应在应用启动时自动启动）"""
    if scheduler_service.is_running():
        raise HTTPException(status_code=400, detail="调度器已在运行中")

    # APScheduler 4.x 中调度器应在 lifespan 中启动
    raise HTTPException(status_code=400, detail="请重启应用以启动调度器")


@router.post("/shutdown", response_model=ResponseModel, summary="关闭调度器")
async def shutdown_scheduler():
    """关闭调度器（注意：调度器会在应用关闭时自动关闭）"""
    if not scheduler_service.is_running():
        raise HTTPException(status_code=400, detail="调度器未运行")

    # APScheduler 4.x 中调度器应在 lifespan 中关闭
    raise HTTPException(status_code=400, detail="请关闭应用以停止调度器")


@router.post("/pause", response_model=ResponseModel, summary="暂停调度器")
async def pause_scheduler():
    """暂停调度器（暂不支持）"""
    raise HTTPException(status_code=400, detail="APScheduler 4.x 暂不支持暂停整个调度器")


@router.post("/resume", response_model=ResponseModel, summary="恢复调度器")
async def resume_scheduler():
    """恢复调度器（暂不支持）"""
    raise HTTPException(status_code=400, detail="APScheduler 4.x 暂不支持恢复整个调度器")


@router.get("/status", response_model=SchedulerStatusOut, summary="获取调度器状态")
async def get_scheduler_status():
    """获取调度器状态"""
    is_running = scheduler_service.is_running()
    jobs = await scheduler_service.get_all_jobs() if is_running else []

    return SchedulerStatusOut(
        is_running=is_running,
        job_count=len(jobs),
        jobs=jobs,
    )


@router.get("/log/{log_id}/stream", summary="实时日志流")
async def stream_task_log(log_id: str):
    """
    通过 SSE 实时推送任务执行日志
    
    Args:
        log_id: 日志记录 ID
        
    Returns:
        SSE 事件流，包含任务执行过程中的日志消息
    """
    from fastapi.responses import StreamingResponse
    from scheduler.task_log_service import TaskLogService
    import json
    
    async def event_generator():
        try:
            async for log_entry in TaskLogService.subscribe(log_id):
                yield f"data: {json.dumps(log_entry, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'level': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
