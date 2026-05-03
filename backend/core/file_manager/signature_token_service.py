#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
签名令牌服务
用于手机扫码签名功能
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.file_manager.signature_token_model import SignatureToken


class SignatureTokenService:
    """签名令牌服务"""

    @staticmethod
    def generate_token() -> str:
        """生成随机令牌"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_callback_key() -> str:
        """生成回调标识"""
        return secrets.token_urlsafe(16)

    @classmethod
    async def create_token(
        cls,
        db: AsyncSession,
        source: str = "form",
        expire_minutes: int = 30,
        user_id: Optional[str] = None,
    ) -> SignatureToken:
        """
        创建签名令牌
        
        Args:
            db: 数据库会话
            source: 来源(form/workflow等)
            expire_minutes: 过期时间（分钟），默认30分钟
            user_id: 创建用户ID
        
        Returns:
            SignatureToken: 签名令牌对象
        """
        token = cls.generate_token()
        callback_key = cls.generate_callback_key()
        expired_at = datetime.now() + timedelta(minutes=expire_minutes)

        token_obj = SignatureToken(
            token=token,
            callback_key=callback_key,
            source=source,
            expired_at=expired_at,
            user_id=user_id,
        )
        db.add(token_obj)
        await db.commit()
        await db.refresh(token_obj)
        return token_obj

    @classmethod
    async def get_by_token(
        cls,
        db: AsyncSession,
        token: str,
    ) -> Optional[SignatureToken]:
        """
        根据令牌获取签名令牌对象
        
        Args:
            db: 数据库会话
            token: 令牌字符串
        
        Returns:
            Optional[SignatureToken]: 签名令牌对象
        """
        query = select(SignatureToken).where(
            SignatureToken.token == token,
            SignatureToken.is_deleted == False,  # noqa: E712
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_callback_key(
        cls,
        db: AsyncSession,
        callback_key: str,
    ) -> Optional[SignatureToken]:
        """
        根据回调标识获取签名令牌对象
        
        Args:
            db: 数据库会话
            callback_key: 回调标识
        
        Returns:
            Optional[SignatureToken]: 签名令牌对象
        """
        query = select(SignatureToken).where(
            SignatureToken.callback_key == callback_key,
            SignatureToken.is_deleted == False,  # noqa: E712
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    def validate_token(cls, sign_token: SignatureToken) -> Tuple[bool, str]:
        """
        验证令牌有效性
        
        Args:
            sign_token: 签名令牌对象
        
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if sign_token.is_used:
            return False, "该签名链接已被使用"

        if sign_token.expired_at < datetime.now():
            return False, "该签名链接已过期"

        return True, ""

    @classmethod
    async def complete_signature(
        cls,
        db: AsyncSession,
        sign_token: SignatureToken,
        signature_file_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SignatureToken:
        """
        完成签名
        
        Args:
            db: 数据库会话
            sign_token: 签名令牌对象
            signature_file_id: 签名文件ID
            ip_address: IP地址
            user_agent: 设备信息
        
        Returns:
            SignatureToken: 更新后的签名令牌对象
        """
        sign_token.is_used = True
        sign_token.used_at = datetime.now()
        sign_token.signature_file_id = signature_file_id
        sign_token.ip_address = ip_address
        sign_token.user_agent = user_agent[:500] if user_agent else None

        await db.commit()
        await db.refresh(sign_token)
        return sign_token

    @classmethod
    async def check_signature_status(
        cls,
        db: AsyncSession,
        callback_key: str,
    ) -> dict:
        """
        检查签名状态（用于前端轮询）
        
        Args:
            db: 数据库会话
            callback_key: 回调标识
        
        Returns:
            dict: 签名状态信息
        """
        sign_token = await cls.get_by_callback_key(db, callback_key)
        
        if not sign_token:
            return {
                "status": "not_found",
                "message": "签名令牌不存在",
            }
        
        if sign_token.is_used and sign_token.signature_file_id:
            return {
                "status": "completed",
                "message": "签名已完成",
                "file_id": sign_token.signature_file_id,
            }
        
        if sign_token.expired_at < datetime.now():
            return {
                "status": "expired",
                "message": "签名链接已过期",
            }
        
        return {
            "status": "pending",
            "message": "等待签名",
        }
