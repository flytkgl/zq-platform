#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler Task Utils - 定时任务工具函数
提供任务执行中常用的工具函数
"""
import logging

logger = logging.getLogger(__name__)


class TaskLoggerWrapper:
    """
    任务日志包装器
    
    同时输出日志到控制台和实时推送到前端
    """
    
    def __init__(self, job_code: str, task_logger=None):
        """
        初始化日志包装器
        
        Args:
            job_code: 任务编码
            task_logger: TaskLogger 实例（可选）
        """
        self.job_code = job_code
        self.task_logger = task_logger
    
    async def info(self, message: str):
        """记录信息日志"""
        logger.info(f"[{self.job_code}] {message}")
        if self.task_logger:
            await self.task_logger.info(message)
    
    async def warning(self, message: str):
        """记录警告日志"""
        logger.warning(f"[{self.job_code}] {message}")
        if self.task_logger:
            await self.task_logger.warning(message)
    
    async def error(self, message: str):
        """记录错误日志"""
        logger.error(f"[{self.job_code}] {message}")
        if self.task_logger:
            await self.task_logger.error(message)
    
    async def debug(self, message: str):
        """记录调试日志"""
        logger.debug(f"[{self.job_code}] {message}")
        if self.task_logger:
            await self.task_logger.debug(message)
