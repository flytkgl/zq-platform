# -*- coding: utf-8 -*-
"""
通知 WebSocket 消费者
"""
from typing import Dict, Any

from fastapi import WebSocket

from core.websocket.consumers.base import TokenAuthWebSocketConsumer, manager


class NotificationConsumer(TokenAuthWebSocketConsumer):
    """通知WebSocket消费者"""
    
    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
    
    async def connect(self):
        """连接并加入通知组"""
        await super().connect()
        if self.is_authenticated and self.user_id:
            # 加入用户通知组
            await manager.group_add(
                f"notifications_user_{self.user_id}",
                self.websocket
            )
    
    async def disconnect(self, close_code: int = 1000):
        """断开连接并离开通知组"""
        if self.user_id:
            await manager.group_discard(
                f"notifications_user_{self.user_id}",
                self.websocket
            )
        await super().disconnect(close_code)
    
    async def handle_message(self, data: Dict[str, Any]):
        """处理通知相关消息"""
        message_type = data.get('type', 'unknown')
        
        if message_type == 'subscribe':
            await self.send_message('subscribe_response', '已订阅通知')
        else:
            await self.send_message('notification_response', f'通知消息处理: {message_type}')
    
    async def notification_message(self, event: Dict[str, Any]):
        """处理组广播的通知消息"""
        await self.send_message('notification', event['message'], event.get('data'))
