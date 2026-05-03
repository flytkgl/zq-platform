# -*- coding: utf-8 -*-
"""
WebSocket 路由
定义 WebSocket 端点
"""
from fastapi import APIRouter, WebSocket

from core.websocket.consumers import (
    TestWebSocketConsumer,
    NotificationConsumer,
    ServerMonitorConsumer,
    RedisMonitorConsumer,
    DatabaseMonitorConsumer,
)
from core.chat.ws import ChatConsumer

router = APIRouter(redirect_slashes=False)


@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """WebSocket测试连接"""
    consumer = TestWebSocketConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """通知推送连接"""
    consumer = NotificationConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/notification")
async def websocket_notification(websocket: WebSocket):
    """通知推送连接（兼容路径）"""
    consumer = NotificationConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/notification/")
async def websocket_notification_slash(websocket: WebSocket):
    """通知推送连接（带斜杠兼容）"""
    consumer = NotificationConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/notifications/")
async def websocket_notifications_slash(websocket: WebSocket):
    """通知推送连接（复数带斜杠兼容）"""
    consumer = NotificationConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/server-monitor")
async def websocket_server_monitor(websocket: WebSocket):
    """服务器监控连接"""
    consumer = ServerMonitorConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/server-monitor/")
async def websocket_server_monitor_slash(websocket: WebSocket):
    """服务器监控连接（带斜杠兼容）"""
    consumer = ServerMonitorConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/redis-monitor")
async def websocket_redis_monitor(websocket: WebSocket):
    """Redis监控连接"""
    consumer = RedisMonitorConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/redis-monitor/")
async def websocket_redis_monitor_slash(websocket: WebSocket):
    """Redis监控连接（带斜杠兼容）"""
    consumer = RedisMonitorConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/database-monitor")
async def websocket_database_monitor(websocket: WebSocket):
    """数据库监控连接"""
    consumer = DatabaseMonitorConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/database-monitor/")
async def websocket_database_monitor_slash(websocket: WebSocket):
    """数据库监控连接（带斜杠兼容）"""
    consumer = DatabaseMonitorConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """聊天连接"""
    consumer = ChatConsumer(websocket)
    await consumer.run()


@router.websocket("/ws/chat/")
async def websocket_chat_slash(websocket: WebSocket):
    """聊天连接（带斜杠兼容）"""
    consumer = ChatConsumer(websocket)
    await consumer.run()
