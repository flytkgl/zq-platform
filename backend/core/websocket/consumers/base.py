# -*- coding: utf-8 -*-
"""
WebSocket 基础消费者类
提供 Token 认证和基础消息处理功能
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Set
from urllib.parse import parse_qs

from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings
from utils.security import verify_access_token

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 活跃连接: {user_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # 组连接: {group_name: {websocket1, websocket2, ...}}
        self.groups: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """添加连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """移除连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # 从所有组中移除
        for group_name in list(self.groups.keys()):
            self.groups[group_name].discard(websocket)
            if not self.groups[group_name]:
                del self.groups[group_name]
    
    async def group_add(self, group_name: str, websocket: WebSocket):
        """将连接添加到组"""
        if group_name not in self.groups:
            self.groups[group_name] = set()
        self.groups[group_name].add(websocket)
    
    async def group_discard(self, group_name: str, websocket: WebSocket):
        """从组中移除连接"""
        if group_name in self.groups:
            self.groups[group_name].discard(websocket)
            if not self.groups[group_name]:
                del self.groups[group_name]
    
    async def broadcast_to_group(self, group_name: str, message: dict):
        """向组内所有连接广播消息"""
        if group_name in self.groups:
            message_text = json.dumps(message)
            for websocket in list(self.groups[group_name]):
                try:
                    await websocket.send_text(message_text)
                except Exception:
                    pass
    
    async def send_to_user(self, user_id: str, message: dict):
        """向指定用户的所有连接发送消息"""
        if user_id in self.active_connections:
            message_text = json.dumps(message)
            for websocket in list(self.active_connections[user_id]):
                try:
                    await websocket.send_text(message_text)
                except Exception:
                    pass

    def is_online(self, user_id: str) -> bool:
        """判断用户是否在线（有活跃的WebSocket连接）"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    def get_online_user_ids(self) -> Set[str]:
        """获取所有在线用户ID"""
        return set(self.active_connections.keys())


# 全局连接管理器实例
manager = ConnectionManager()


class TokenAuthWebSocketConsumer:
    """基于Token认证的WebSocket消费者基类"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.user_id: Optional[str] = None
        self.is_authenticated = False
        self._token: Optional[str] = None  # 保存原始token用于心跳校验
    
    async def authenticate(self) -> bool:
        """
        进行Token认证
        从查询参数中获取token并验证
        """
        # 获取查询参数中的token
        query_string = self.websocket.scope.get('query_string', b'').decode('utf-8')
        token = None
        
        if query_string:
            query_params = parse_qs(query_string)
            token_list = query_params.get('token', [])
            if token_list:
                token = token_list[0]
        
        if not token:
            logger.warning("WebSocket connection rejected: No token provided")
            # 必须先accept才能close
            await self.websocket.accept()
            await self.websocket.close(code=4001)
            return False
        
        # 验证token
        try:
            payload = verify_access_token(token)
            
            if not payload:
                logger.warning("WebSocket connection rejected: Invalid token")
                await self.websocket.accept()
                await self.websocket.close(code=4001)
                return False
            
            user_id = payload.get('sub')
            if not user_id:
                logger.warning("WebSocket connection rejected: Invalid token payload")
                await self.websocket.accept()
                await self.websocket.close(code=4001)
                return False
            
            self.user_id = user_id
            self.is_authenticated = True
            self._token = token  # 保存token用于后续心跳校验
            logger.info(f"WebSocket connection accepted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {str(e)}")
            await self.websocket.accept()
            await self.websocket.close(code=4001)
            return False
    
    async def connect(self):
        """连接时进行Token认证"""
        if await self.authenticate():
            await manager.connect(self.websocket, self.user_id)
    
    async def disconnect(self, close_code: int = 1000):
        """断开连接"""
        if self.user_id:
            manager.disconnect(self.websocket, self.user_id)
        logger.info(f"WebSocket disconnected with code {close_code}")
    
    async def receive(self, text_data: str):
        """接收消息的基础处理"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            # 根据消息类型处理
            if message_type == 'ping':
                await self._handle_ping(data)
            else:
                await self.handle_message(data)
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")
            await self.send_error(f'处理消息时出错: {str(e)}')
    
    async def handle_message(self, data: Dict[str, Any]):
        """子类需要实现的消息处理方法"""
        await self.send_error('Message type not supported')
    
    async def send_message(self, message_type: str, message: str, data: Optional[Dict] = None):
        """发送消息"""
        response = {
            'type': message_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if data:
            response['data'] = data
        
        await self.websocket.send_text(json.dumps(response))
    
    async def send_error(self, error_message: str):
        """发送错误消息"""
        await self.send_message('error', error_message)
    
    async def _handle_ping(self, data: Dict[str, Any]):
        """
        处理心跳ping消息
        同时校验token是否仍然有效，过期则通知前端并关闭连接
        """
        if not self._token:
            await self.send_message('pong', '心跳响应')
            return
        
        # 重新验证token有效性
        payload = verify_access_token(self._token)
        if not payload:
            logger.warning(f"WebSocket token expired for user {self.user_id}")
            await self.send_message('token_expired', 'Access token已过期，请刷新token后重连')
            # 使用4002关闭码表示token过期（区别于4001认证失败）
            await self.websocket.close(code=4002)
            return
        
        await self.send_message('pong', '心跳响应')
    
    async def run(self):
        """运行WebSocket消费者的主循环"""
        await self.connect()
        
        if not self.is_authenticated:
            return
        
        try:
            while True:
                text_data = await self.websocket.receive_text()
                await self.receive(text_data)
        except WebSocketDisconnect as e:
            await self.disconnect(e.code)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            await self.disconnect(1011)
