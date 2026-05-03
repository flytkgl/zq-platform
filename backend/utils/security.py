#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Security Utils - JWT Token工具
用于生成和验证JWT Token
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

# OAuth2密码流，指定token获取地址（auto_error=False让中间件处理认证）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/core/auth/login/oauth2", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, device_id: Optional[str] = None) -> str:
    """
    创建Access Token
    
    :param data: 要编码的数据
    :param expires_delta: 过期时间增量
    :param device_id: 设备唯一标识（可选）
    :return: JWT Token字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    # 如果提供了 device_id，添加到 token 中
    if device_id:
        to_encode["device_id"] = device_id
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None, device_id: Optional[str] = None) -> str:
    """
    创建Refresh Token
    
    :param data: 要编码的数据
    :param expires_delta: 过期时间增量
    :param device_id: 设备标识（用于多设备登录）
    :return: JWT Token字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    # 如果提供了 device_id，添加到 token 中
    if device_id:
        to_encode["device_id"] = device_id
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    解码JWT Token
    
    :param token: JWT Token字符串
    :return: 解码后的数据或None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[dict]:
    """
    验证Access Token
    
    :param token: JWT Token字符串
    :return: 解码后的数据或None（如果无效或不是access token）
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    验证Refresh Token
    
    :param token: JWT Token字符串
    :return: 解码后的数据或None（如果无效或不是refresh token）
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取当前登录用户的依赖函数
    
    注意：此依赖配合AuthMiddleware使用
    - 中间件负责验证token有效性
    - 此依赖从request.state获取用户ID，然后查询完整用户对象
    
    :param request: 请求对象
    :param token: JWT Token（用于Swagger显示锁图标）
    :param db: 数据库会话
    :return: 当前用户对象
    :raises HTTPException: 如果用户不存在
    """
    # 优先从request.state获取（中间件已验证）
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 延迟导入避免循环依赖
    from core.user.service import UserService
    
    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_user_id(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> str:
    """
    获取当前用户ID的依赖函数（轻量级，不查询数据库）
    
    :param request: 请求对象
    :param token: JWT Token（用于Swagger显示锁图标）
    :return: 当前用户ID
    """
    # 优先从request.state获取（中间件已验证）
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id and token:
        payload = verify_access_token(token)
        if payload:
            user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_active_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取当前活跃用户的依赖函数
    
    :param request: 请求对象
    :param token: JWT Token（用于Swagger显示锁图标）
    :param db: 数据库会话
    :return: 当前活跃用户对象
    :raises HTTPException: 如果用户状态不正常
    """
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id and token:
        payload = verify_access_token(token)
        if payload:
            user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from core.user.service import UserService
    user = await UserService.get_by_id(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    if user.user_status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户状态异常"
        )
    
    return user


async def get_current_superuser(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取当前超级管理员的依赖函数
    
    :param request: 请求对象
    :param token: JWT Token（用于Swagger显示锁图标）
    :param db: 数据库会话
    :return: 当前超级管理员对象
    :raises HTTPException: 如果不是超级管理员
    """
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id and token:
        payload = verify_access_token(token)
        if payload:
            user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    from core.user.service import UserService
    user = await UserService.get_by_id(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    return user
