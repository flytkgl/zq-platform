# -*- coding: utf-8 -*-
"""
测试 WebSocket 消费者
"""
import platform
from datetime import datetime
from typing import Dict, Any

from fastapi import WebSocket

from core.websocket.consumers.base import TokenAuthWebSocketConsumer


class TestWebSocketConsumer(TokenAuthWebSocketConsumer):
    """测试WebSocket消费者"""
    
    def __init__(self, websocket: WebSocket):
        super().__init__(websocket)
    
    async def handle_message(self, data: Dict[str, Any]):
        """处理测试消息"""
        message_type = data.get('type', 'unknown')
        content = data.get('content', '')
        
        if message_type == 'echo':
            await self.send_message('echo_response', f'回声: {content}')
        elif message_type == 'chat':
            await self.send_message('chat_response', f'收到聊天消息: {content}', {
                'user': f'user_{self.user_id}',
                'original_message': content
            })
        elif message_type == 'system_info':
            # 获取系统信息
            system_info = {
                'hostname': platform.node(),
                'system': platform.system(),
                'python_version': platform.python_version(),
                'timestamp': datetime.now().isoformat()
            }
            await self.send_message('system_info_response', '系统信息', system_info)
        else:
            await self.send_message('unknown_response', f'未知消息类型: {message_type}')
