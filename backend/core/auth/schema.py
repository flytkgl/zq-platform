#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auth Schema - 认证相关Schema
"""
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.base_schema import CSTDatetime


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token响应"""
    accessToken: str = Field(..., description="访问令牌")
    refreshToken: str = Field(..., description="刷新令牌")
    tokenType: str = Field(default="bearer", description="令牌类型")
    expireTime: int = Field(..., description="访问令牌过期时间（秒）")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenData(BaseModel):
    """Token数据"""
    user_id: Optional[str] = None
    username: Optional[str] = None


class LoginUserInfo(BaseModel):
    """登录用户信息"""
    id: str
    username: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    avatar: Optional[str] = None
    name: Optional[str] = None
    gender: int = 0
    gender_display: Optional[str] = None
    user_type: int = 1
    user_type_display: Optional[str] = None
    user_status: int = 1
    user_status_display: Optional[str] = None
    birthday: Optional[date] = None
    city: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    is_superuser: bool = False
    is_active: bool = True
    dept_id: Optional[str] = None
    post_id: Optional[str] = None
    post_name: Optional[str] = None
    manager_id: Optional[str] = None
    role_ids: Optional[List[str]] = None
    last_login: Optional[CSTDatetime] = None
    last_login_ip: Optional[str] = None
    last_login_type: Optional[str] = None
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """登录响应"""
    user: LoginUserInfo = Field(..., description="用户信息")
    token: TokenResponse = Field(..., description="令牌信息")
