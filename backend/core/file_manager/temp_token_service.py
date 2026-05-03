#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
临时访问令牌服务
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.file_manager.temp_token_model import FileAccessToken


class FileAccessTokenService:
    """文件临时访问令牌服务"""

    @staticmethod
    def generate_token() -> str:
        """生成随机令牌"""
        return secrets.token_urlsafe(48)

    @classmethod
    async def create_token(
        cls,
        db: AsyncSession,
        file_id: str,
        expires_in_seconds: int = 3600,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> FileAccessToken:
        """
        创建临时访问令牌
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            expires_in_seconds: 过期时间（秒），默认1小时
            user_id: 用户ID
            ip_address: IP地址
            user_agent: User Agent
        
        Returns:
            FileAccessToken: 临时访问令牌对象
        """
        token = cls.generate_token()
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)

        token_obj = FileAccessToken(
            token=token,
            file_id=file_id,
            expires_at=expires_at,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(token_obj)
        await db.commit()
        await db.refresh(token_obj)
        return token_obj

    @classmethod
    async def verify_token(
        cls,
        db: AsyncSession,
        token: str,
    ) -> Optional[FileAccessToken]:
        """
        验证令牌并返回令牌对象
        
        Args:
            db: 数据库会话
            token: 令牌字符串
        
        Returns:
            Optional[FileAccessToken]: 如果令牌有效返回令牌对象，否则返回None
        """
        query = select(FileAccessToken).where(
            FileAccessToken.token == token,
            FileAccessToken.is_deleted == False,  # noqa: E712
            FileAccessToken.expires_at > datetime.utcnow(),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def revoke_token(
        cls,
        db: AsyncSession,
        token: str,
    ) -> bool:
        """
        撤销令牌（软删除）
        
        Args:
            db: 数据库会话
            token: 令牌字符串
        
        Returns:
            bool: 是否成功撤销
        """
        query = select(FileAccessToken).where(
            FileAccessToken.token == token,
            FileAccessToken.is_deleted == False,  # noqa: E712
        )
        result = await db.execute(query)
        token_obj = result.scalar_one_or_none()
        
        if token_obj:
            token_obj.is_deleted = True
            await db.commit()
            return True
        return False

    @classmethod
    async def cleanup_expired_tokens(
        cls,
        db: AsyncSession,
    ) -> int:
        """
        清理过期的令牌（物理删除）
        
        Args:
            db: 数据库会话
        
        Returns:
            int: 清理的令牌数量
        """
        stmt = delete(FileAccessToken).where(
            FileAccessToken.expires_at < datetime.utcnow()
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    @classmethod
    async def get_file_tokens(
        cls,
        db: AsyncSession,
        file_id: str,
        include_expired: bool = False,
    ) -> list[FileAccessToken]:
        """
        获取文件的所有令牌
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            include_expired: 是否包含过期的令牌
        
        Returns:
            list[FileAccessToken]: 令牌列表
        """
        conditions = [
            FileAccessToken.file_id == file_id,
            FileAccessToken.is_deleted == False,  # noqa: E712
        ]
        
        if not include_expired:
            conditions.append(FileAccessToken.expires_at > datetime.utcnow())
        
        query = select(FileAccessToken).where(*conditions)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def revoke_file_tokens(
        cls,
        db: AsyncSession,
        file_id: str,
    ) -> int:
        """
        撤销文件的所有令牌
        
        Args:
            db: 数据库会话
            file_id: 文件ID
        
        Returns:
            int: 撤销的令牌数量
        """
        query = select(FileAccessToken).where(
            FileAccessToken.file_id == file_id,
            FileAccessToken.is_deleted == False,  # noqa: E712
        )
        result = await db.execute(query)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.is_deleted = True
            count += 1
        
        await db.commit()
        return count
