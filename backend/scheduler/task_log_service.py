#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务执行日志服务
通过 Redis Pub/Sub 实现任务执行过程中的实时日志推送
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

from utils.redis import RedisClient


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class TaskLogEntry:
    """任务日志条目"""
    timestamp: str
    level: str
    message: str
    step: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    data: Optional[dict] = None
    
    def to_dict(self) -> dict:
        result = asdict(self)
        # 移除 None 值
        return {k: v for k, v in result.items() if v is not None}


class TaskLogService:
    """
    任务日志服务
    
    用于在任务执行过程中发布实时日志，前端通过 SSE 订阅
    使用 Redis List 存储历史日志 + Pub/Sub 推送新消息
    """
    
    # Redis 频道前缀
    CHANNEL_PREFIX = "scheduler:task_log:"
    # Redis List 前缀（存储历史日志）
    LIST_PREFIX = "scheduler:task_log_history:"
    # 日志过期时间（秒）- 1小时
    LOG_EXPIRE_SECONDS = 3600
    
    @classmethod
    def _get_channel(cls, log_id: str) -> str:
        """获取 Redis Pub/Sub 频道名称"""
        return f"{cls.CHANNEL_PREFIX}{log_id}"
    
    @classmethod
    def _get_list_key(cls, log_id: str) -> str:
        """获取 Redis List 键名"""
        return f"{cls.LIST_PREFIX}{log_id}"
    
    @classmethod
    async def publish(
        cls,
        log_id: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        step: Optional[str] = None,
        progress: Optional[int] = None,
        data: Optional[dict] = None
    ):
        """
        发布日志消息
        
        同时存储到 Redis List（历史）和发布到 Pub/Sub（实时）
        
        Args:
            log_id: 日志记录 ID
            message: 日志消息
            level: 日志级别
            step: 当前步骤名称
            progress: 进度百分比 (0-100)
            data: 附加数据
        """
        try:
            redis = await RedisClient.get_client()
        except Exception:
            return
        
        entry = TaskLogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            message=message,
            step=step,
            progress=progress,
            data=data
        )
        
        entry_json = json.dumps(entry.to_dict(), ensure_ascii=False)
        list_key = cls._get_list_key(log_id)
        channel = cls._get_channel(log_id)
        
        # 存储到 List（历史日志）
        await redis.rpush(list_key, entry_json)
        # 设置过期时间
        await redis.expire(list_key, cls.LOG_EXPIRE_SECONDS)
        # 发布到 Pub/Sub（实时推送）
        await redis.publish(channel, entry_json)
    
    @classmethod
    async def publish_start(cls, log_id: str, job_name: str):
        """发布任务开始事件"""
        await cls.publish(
            log_id=log_id,
            message=f"任务 {job_name} 开始执行",
            level=LogLevel.INFO,
            step="start",
            progress=0
        )
    
    @classmethod
    async def publish_complete(cls, log_id: str, job_name: str, result: Optional[str] = None):
        """发布任务完成事件"""
        await cls.publish(
            log_id=log_id,
            message=f"任务 {job_name} 执行完成",
            level=LogLevel.SUCCESS,
            step="complete",
            progress=100,
            data={"result": result} if result else None
        )
    
    @classmethod
    async def publish_error(cls, log_id: str, job_name: str, error: str):
        """发布任务错误事件"""
        await cls.publish(
            log_id=log_id,
            message=f"任务 {job_name} 执行失败: {error}",
            level=LogLevel.ERROR,
            step="error",
            data={"error": error}
        )
    
    @classmethod
    async def get_history(cls, log_id: str) -> list:
        """
        获取历史日志
        
        Args:
            log_id: 日志记录 ID
            
        Returns:
            日志条目列表
        """
        try:
            redis = await RedisClient.get_client()
        except Exception:
            return []
        
        list_key = cls._get_list_key(log_id)
        entries = await redis.lrange(list_key, 0, -1)
        
        result = []
        for entry_json in entries:
            try:
                result.append(json.loads(entry_json))
            except json.JSONDecodeError:
                pass
        
        return result
    
    @classmethod
    async def subscribe(cls, log_id: str) -> AsyncGenerator[dict, None]:
        """
        订阅日志消息
        
        先返回历史日志，然后订阅新消息
        
        Args:
            log_id: 日志记录 ID
            
        Yields:
            日志条目字典
        """
        try:
            redis = await RedisClient.get_client()
        except Exception:
            return
        
        list_key = cls._get_list_key(log_id)
        channel = cls._get_channel(log_id)
        
        # 先获取历史日志
        history = await redis.lrange(list_key, 0, -1)
        
        # 返回历史日志
        for entry_json in history:
            try:
                data = json.loads(entry_json)
                yield data
                
                # 如果历史日志中已经有完成或错误事件，直接结束
                if data.get("step") in ("complete", "error"):
                    return
            except json.JSONDecodeError:
                pass
        
        # 订阅新消息
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    yield data
                    
                    # 如果是完成或错误事件，结束订阅
                    if data.get("step") in ("complete", "error"):
                        break
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()


class TaskLogger:
    """
    任务日志记录器
    
    在任务函数中使用，用于记录执行过程中的日志
    """
    
    def __init__(self, log_id: str, job_name: str = ""):
        self.log_id = log_id
        self.job_name = job_name
        self._current_step = None
        self._progress = 0
    
    async def debug(self, message: str, **kwargs):
        """记录调试日志"""
        await TaskLogService.publish(
            log_id=self.log_id,
            message=message,
            level=LogLevel.DEBUG,
            step=self._current_step,
            progress=self._progress,
            **kwargs
        )
    
    async def info(self, message: str, **kwargs):
        """记录信息日志"""
        await TaskLogService.publish(
            log_id=self.log_id,
            message=message,
            level=LogLevel.INFO,
            step=self._current_step,
            progress=self._progress,
            **kwargs
        )
    
    async def warning(self, message: str, **kwargs):
        """记录警告日志"""
        await TaskLogService.publish(
            log_id=self.log_id,
            message=message,
            level=LogLevel.WARNING,
            step=self._current_step,
            progress=self._progress,
            **kwargs
        )
    
    async def error(self, message: str, **kwargs):
        """记录错误日志"""
        await TaskLogService.publish(
            log_id=self.log_id,
            message=message,
            level=LogLevel.ERROR,
            step=self._current_step,
            progress=self._progress,
            **kwargs
        )
    
    async def success(self, message: str, **kwargs):
        """记录成功日志"""
        await TaskLogService.publish(
            log_id=self.log_id,
            message=message,
            level=LogLevel.SUCCESS,
            step=self._current_step,
            progress=self._progress,
            **kwargs
        )
    
    def set_step(self, step: str):
        """设置当前步骤"""
        self._current_step = step
    
    def set_progress(self, progress: int):
        """设置进度 (0-100)"""
        self._progress = max(0, min(100, progress))
    
    async def step(self, step: str, message: str, progress: Optional[int] = None):
        """
        记录步骤日志
        
        Args:
            step: 步骤名称
            message: 日志消息
            progress: 进度百分比
        """
        self._current_step = step
        if progress is not None:
            self._progress = progress
        
        await self.info(message, step=step, progress=self._progress)
