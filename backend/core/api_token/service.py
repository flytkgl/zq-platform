#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Token Service
"""
import hashlib
import secrets
from datetime import datetime, timezone, UTC
from typing import Optional, List, Tuple

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.api_token.model import ApiToken

TOKEN_PREFIX = "zqpat_"


def generate_token() -> str:
    """生成随机API Token"""
    return TOKEN_PREFIX + secrets.token_hex(32)


def hash_token(token: str) -> str:
    """对token进行SHA-256哈希"""
    return hashlib.sha256(token.encode()).hexdigest()


def get_token_display_prefix(token: str) -> str:
    """获取token的展示前缀（前12位 + ...）"""
    return token[:12] + "..."


class ApiTokenService:
    """API Token 服务层"""

    @classmethod
    async def create_token(
        cls,
        db: AsyncSession,
        user_id: str,
        name: str,
        expires_at: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> Tuple[ApiToken, str]:
        """
        创建API Token

        :return: (数据库记录, 明文token) - 明文token仅返回一次
        """
        raw_token = generate_token()

        db_obj = ApiToken(
            name=name,
            token_hash=hash_token(raw_token),
            token_prefix=get_token_display_prefix(raw_token),
            user_id=user_id,
            expires_at=expires_at,
            description=description,
            is_active=True,
            sys_creator_id=user_id,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj, raw_token

    @classmethod
    async def get_user_tokens(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> List[ApiToken]:
        """获取用户的所有API Token"""
        result = await db.execute(
            select(ApiToken)
            .where(
                ApiToken.user_id == user_id,
                ApiToken.is_deleted == False,  # noqa: E712
            )
            .order_by(desc(ApiToken.sys_create_datetime))
        )
        return list(result.scalars().all())

    @classmethod
    async def get_token_by_id(
        cls,
        db: AsyncSession,
        token_id: str,
        user_id: str,
    ) -> Optional[ApiToken]:
        """根据ID获取Token（限定用户）"""
        result = await db.execute(
            select(ApiToken).where(
                ApiToken.id == token_id,
                ApiToken.user_id == user_id,
                ApiToken.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def revoke_token(
        cls,
        db: AsyncSession,
        token_id: str,
        user_id: str,
    ) -> bool:
        """撤销（软删除）Token"""
        token = await cls.get_token_by_id(db, token_id, user_id)
        if not token:
            return False
        token.is_deleted = True
        token.is_active = False
        await db.commit()
        return True

    @classmethod
    async def verify_token(
        cls,
        db: AsyncSession,
        raw_token: str,
    ) -> Optional[ApiToken]:
        """
        验证API Token

        :return: 有效则返回Token记录，否则返回None
        """
        token_hash_value = hash_token(raw_token)
        result = await db.execute(
            select(ApiToken).where(
                ApiToken.token_hash == token_hash_value,
                ApiToken.is_deleted == False,  # noqa: E712
                ApiToken.is_active == True,  # noqa: E712
            )
        )
        token = result.scalar_one_or_none()
        if not token:
            return None

        now_utc = datetime.now(UTC)
        if token.expires_at:
            expires = token.expires_at if token.expires_at.tzinfo else token.expires_at.replace(tzinfo=UTC)
            if expires < now_utc:
                return None

        token.last_used_at = now_utc.replace(tzinfo=None)
        await db.commit()
        return token
