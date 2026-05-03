# -*- coding: utf-8 -*-
"""
数据库监控 WebSocket 消费者
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from fastapi import WebSocket

from core.websocket.consumers.base import TokenAuthWebSocketConsumer, manager

logger = logging.getLogger(__name__)


class DatabaseMonitorConsumer(TokenAuthWebSocketConsumer):
    """数据库监控WebSocket消费者"""
    
    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        self.monitor_interval = 2  # 固定2秒更新一次
        self.current_db_name: Optional[str] = None
    
    async def connect(self):
        """连接并开始监控"""
        await super().connect()
        if self.is_authenticated and self.user_id:
            # 加入数据库监控组
            await manager.group_add(
                "database_monitor",
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
                "database_monitor",
                self.websocket
            )
        await super().disconnect(close_code)
    
    async def handle_message(self, data: Dict[str, Any]):
        """处理数据库监控消息"""
        message_type = data.get('type', 'unknown')
        
        if message_type == 'start_monitor':
            db_name = data.get('db_name')
            if not db_name:
                await self.send_error('缺少数据库名称参数')
                return
            await self.start_monitoring(db_name)
        elif message_type == 'stop_monitor':
            await self.stop_monitoring()
        elif message_type == 'get_overview':
            db_name = data.get('db_name')
            if not db_name:
                await self.send_error('缺少数据库名称参数')
                return
            await self.send_database_overview(db_name)
        elif message_type == 'get_realtime':
            db_name = data.get('db_name')
            if not db_name:
                await self.send_error('缺少数据库名称参数')
                return
            await self.send_realtime_stats(db_name)
        elif message_type == 'test_connection':
            db_name = data.get('db_name')
            if not db_name:
                await self.send_error('缺少数据库名称参数')
                return
            await self.test_database_connection(db_name)
        elif message_type == 'get_configs':
            await self.send_database_configs()
        else:
            await self.send_error(f'未知的数据库监控命令: {message_type}')
    
    async def start_monitoring(self, db_name: str):
        """开始监控"""
        if self.is_monitoring:
            await self.send_message('monitor_status', '数据库监控已在运行')
            return
        
        self.current_db_name = db_name
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self.monitor_loop())
        await self.send_message('monitor_started', f'开始数据库监控({db_name})，间隔{self.monitor_interval}秒')
    
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
        self.current_db_name = None
        await self.send_message('monitor_stopped', '数据库监控已停止')
    
    async def restart_monitoring(self):
        """重启监控"""
        if self.current_db_name:
            db_name = self.current_db_name
            await self.stop_monitoring()
            await asyncio.sleep(0.1)  # 短暂延迟
            await self.start_monitoring(db_name)
    
    async def monitor_loop(self):
        """监控循环"""
        try:
            while self.is_monitoring and self.current_db_name:
                try:
                    await self.send_realtime_stats(self.current_db_name)
                except Exception as e:
                    logger.error(f"发送数据库实时数据失败: {str(e)}")
                    # 发送错误消息但不停止监控循环
                    try:
                        await self.send_error(f'获取数据库监控数据失败: {str(e)}')
                    except:
                        pass
                
                # 等待下一次监控间隔
                await asyncio.sleep(self.monitor_interval)
        except asyncio.CancelledError:
            logger.info("数据库监控循环被取消")
        except Exception as e:
            logger.error(f"数据库监控循环严重错误: {str(e)}")
            self.is_monitoring = False
    
    def _get_database_configs(self):
        """获取数据库配置列表"""
        try:
            from core.database_monitor import get_database_configs
            return get_database_configs()
        except ImportError:
            logger.warning("database_monitor module not available")
            return []
    
    def _get_database_collector(self, db_config: Dict[str, Any]):
        """获取数据库收集器"""
        try:
            from core.database_monitor import DatabaseCollector
            return DatabaseCollector(
                db_type=db_config['db_type'],
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
        except ImportError:
            logger.warning("DatabaseCollector not available")
            return None
    
    async def send_database_configs(self):
        """发送数据库配置列表"""
        try:
            # 在线程池中执行同步方法
            loop = asyncio.get_event_loop()
            configs = await loop.run_in_executor(None, self._get_database_configs)
            
            await self.send_message('database_configs', '数据库配置列表', configs)
        except Exception as e:
            logger.error(f"获取数据库配置失败: {str(e)}")
            await self.send_error(f'获取数据库配置失败: {str(e)}')
    
    async def send_database_overview(self, db_name: str):
        """发送数据库概览信息"""
        try:
            # 在线程池中执行同步方法
            loop = asyncio.get_event_loop()
            configs = await loop.run_in_executor(None, self._get_database_configs)
            db_config = next((config for config in configs if config['db_name'] == db_name), None)
            
            if not db_config:
                await self.send_error(f'数据库 {db_name} 未找到')
                return
            
            collector = self._get_database_collector(db_config)
            if collector is None:
                await self.send_error('数据库监控模块未安装')
                return
            
            overview_data = await loop.run_in_executor(
                None,
                collector.get_all_info,
                db_name,
                db_config['name']
            )
            
            await self.send_message('database_overview', '数据库概览信息', overview_data)
        except Exception as e:
            logger.error(f"获取数据库概览失败: {str(e)}")
            await self.send_error(f'获取数据库概览失败: {str(e)}')
    
    async def send_realtime_stats(self, db_name: str):
        """发送数据库实时统计信息"""
        try:
            # 在线程池中执行同步方法
            loop = asyncio.get_event_loop()
            configs = await loop.run_in_executor(None, self._get_database_configs)
            db_config = next((config for config in configs if config['db_name'] == db_name), None)
            
            if not db_config:
                await self.send_error(f'数据库 {db_name} 未找到')
                return
            
            collector = self._get_database_collector(db_config)
            if collector is None:
                await self.send_error('数据库监控模块未安装')
                return
            
            realtime_data = await loop.run_in_executor(
                None,
                collector.get_realtime_stats,
                db_name
            )
            
            await self.send_message('database_realtime', '数据库实时统计', realtime_data)
        except Exception as e:
            logger.error(f"获取数据库实时统计失败: {str(e)}")
            await self.send_error(f'获取数据库实时统计失败: {str(e)}')
    
    async def test_database_connection(self, db_name: str):
        """测试数据库连接"""
        try:
            # 在线程池中执行同步方法
            loop = asyncio.get_event_loop()
            configs = await loop.run_in_executor(None, self._get_database_configs)
            db_config = next((config for config in configs if config['db_name'] == db_name), None)
            
            if not db_config:
                await self.send_error(f'数据库 {db_name} 未找到')
                return
            
            collector = self._get_database_collector(db_config)
            if collector is None:
                await self.send_error('数据库监控模块未安装')
                return
            
            test_result = await loop.run_in_executor(None, collector.test_connection)
            
            await self.send_message('connection_test', '数据库连接测试结果', test_result)
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            await self.send_error(f'数据库连接测试失败: {str(e)}')
