# -*- coding: utf-8 -*-
"""
服务器监控 WebSocket 消费者
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from fastapi import WebSocket

from core.websocket.consumers.base import TokenAuthWebSocketConsumer, manager

logger = logging.getLogger(__name__)


class ServerMonitorConsumer(TokenAuthWebSocketConsumer):
    """服务器监控WebSocket消费者"""
    
    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        self.monitor_interval = 2  # 固定2秒更新一次
        # 创建持久的收集器实例以保持缓存数据
        self.server_collector = None
    
    def _get_server_collector(self):
        """懒加载服务器信息收集器"""
        if self.server_collector is None:
            try:
                from core.server_monitor.server_info import ServerInfoCollector
                self.server_collector = ServerInfoCollector()
            except ImportError:
                logger.warning("ServerInfoCollector not available")
        return self.server_collector
    
    async def connect(self):
        """连接并开始监控"""
        await super().connect()
        if self.is_authenticated and self.user_id:
            # 加入服务器监控组
            await manager.group_add(
                "server_monitor",
                self.websocket
            )
    
    async def disconnect(self, close_code: int = 1000):
        """断开连接并停止监控"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        if self.user_id:
            await manager.group_discard(
                "server_monitor",
                self.websocket
            )
        await super().disconnect(close_code)
    
    async def handle_message(self, data: Dict[str, Any]):
        """处理服务器监控消息"""
        message_type = data.get('type', 'unknown')
        
        if message_type == 'start_monitor':
            await self.start_monitoring()
        elif message_type == 'stop_monitor':
            await self.stop_monitoring()
        elif message_type == 'get_overview':
            await self.send_server_overview()
        elif message_type == 'get_realtime':
            await self.send_realtime_stats()
        else:
            await self.send_error(f'未知的监控命令: {message_type}')
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            await self.send_message('monitor_status', '监控已在运行')
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self.monitor_loop())
        await self.send_message('monitor_started', f'开始监控，间隔{self.monitor_interval}秒')
    
    async def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        await self.send_message('monitor_stopped', '监控已停止')
    
    async def restart_monitoring(self):
        """重启监控"""
        await self.stop_monitoring()
        await asyncio.sleep(0.1)  # 短暂延迟
        await self.start_monitoring()
    
    async def monitor_loop(self):
        """监控循环"""
        try:
            while self.is_monitoring:
                try:
                    await self.send_realtime_stats()
                except Exception as e:
                    logger.error(f"发送实时数据失败: {str(e)}")
                    # 发送错误消息但不停止监控循环
                    try:
                        await self.send_error(f'获取监控数据失败: {str(e)}')
                    except:
                        pass
                
                # 等待下一次监控间隔
                await asyncio.sleep(self.monitor_interval)
        except asyncio.CancelledError:
            logger.info("监控循环被取消")
        except Exception as e:
            logger.error(f"监控循环严重错误: {str(e)}")
            self.is_monitoring = False
    
    async def send_server_overview(self):
        """发送服务器概览信息"""
        try:
            collector = self._get_server_collector()
            if collector is None:
                await self.send_error('服务器监控模块未安装')
                return
            
            # 在线程池中执行同步方法
            loop = asyncio.get_event_loop()
            overview_data = await loop.run_in_executor(None, collector.get_all_info)
            
            await self.send_message('server_overview', '服务器概览信息', overview_data)
        except Exception as e:
            logger.error(f"获取服务器概览失败: {str(e)}")
            await self.send_error(f'获取服务器概览失败: {str(e)}')
    
    async def send_realtime_stats(self):
        """发送实时统计信息"""
        try:
            collector = self._get_server_collector()
            if collector is None:
                await self.send_error('服务器监控模块未安装')
                return
            
            # 在线程池中执行同步方法
            loop = asyncio.get_event_loop()
            realtime_data = await loop.run_in_executor(None, collector.get_realtime_stats)
            
            await self.send_message('realtime_stats', '实时统计信息', realtime_data)
        except Exception as e:
            logger.error(f"获取实时统计失败: {str(e)}")
            await self.send_error(f'获取实时统计失败: {str(e)}')
