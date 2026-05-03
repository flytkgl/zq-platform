#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API Token 路由
个人访问令牌管理
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.base_schema import ResponseModel
from utils.security import get_current_user
from core.api_token.service import ApiTokenService
from core.api_token.schema import (
    ApiTokenCreate,
    ApiTokenResponse,
    ApiTokenCreateResponse,
)

router = APIRouter(prefix="/api-tokens", tags=["API Token管理"])


@router.get("", response_model=List[ApiTokenResponse], summary="获取Token列表")
async def list_tokens(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有API Token"""
    tokens = await ApiTokenService.get_user_tokens(db, current_user.id)
    return tokens


@router.post("", response_model=ApiTokenCreateResponse, summary="创建Token")
async def create_token(
    data: ApiTokenCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的API Token

    注意：完整的Token值仅在创建时返回一次，请妥善保存。
    """
    db_token, raw_token = await ApiTokenService.create_token(
        db=db,
        user_id=current_user.id,
        name=data.name,
        expires_at=data.expires_at,
        description=data.description,
    )
    return ApiTokenCreateResponse(
        id=db_token.id,
        name=db_token.name,
        token=raw_token,
        token_prefix=db_token.token_prefix,
        expires_at=db_token.expires_at,
        description=db_token.description,
        sys_create_datetime=db_token.sys_create_datetime,
    )


@router.delete("/{token_id}", response_model=ResponseModel, summary="撤销Token")
async def revoke_token(
    token_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """撤销指定的API Token"""
    success = await ApiTokenService.revoke_token(db, token_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token不存在",
        )
    return ResponseModel(message="Token已撤销")
