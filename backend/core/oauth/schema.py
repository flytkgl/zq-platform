#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OAuth Schema - OAuth 数据模型
定义 OAuth 相关的请求和响应数据结构
"""
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class OAuthCallbackIn(BaseModel):
    """OAuth 回调请求参数 (通用)"""
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(default=None, description="状态参数")


class AuthorizeUrlOut(BaseModel):
    """授权 URL 响应"""
    authorize_url: str = Field(..., description="OAuth 授权 URL")


class OAuthUserInfo(BaseModel):
    """OAuth 用户信息"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    name: str = Field(..., description="显示名称")
    email: Optional[str] = Field(default=None, description="邮箱")
    avatar: Optional[str] = Field(default=None, description="头像URL")
    user_type: int = Field(default=1, description="用户类型")
    is_superuser: bool = Field(default=False, description="是否超级管理员")


class OAuthLoginOut(BaseModel):
    """OAuth 登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    expire: int = Field(..., description="过期时间(秒)")
    user_info: Dict[str, Any] = Field(..., description="用户信息")
