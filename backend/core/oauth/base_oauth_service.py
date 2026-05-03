#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OAuth 基础服务类
提供通用的 OAuth 认证流程（异步版本）
"""
import logging
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Dict, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from utils.redis import RedisClient
from core.user.model import User
from core.login_log.service import LoginLogService
from utils.security import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)

# Redis中存储refresh token的key前缀
REFRESH_TOKEN_PREFIX = "refresh_token:"


class BaseOAuthService(ABC):
    """OAuth 服务基类"""

    # 子类需要定义这些属性
    PROVIDER_NAME: str = None  # 提供商名称，如 'gitee', 'github'
    AUTHORIZE_URL: str = None  # 授权 URL
    TOKEN_URL: str = None  # 获取 token 的 URL
    USER_INFO_URL: str = None  # 获取用户信息的 URL

    @classmethod
    @abstractmethod
    def get_client_config(cls) -> Dict[str, str]:
        """
        获取客户端配置
        
        Returns:
            Dict: 包含 client_id, client_secret, redirect_uri
        """
        pass

    @classmethod
    def get_authorize_url(cls, state: str = None) -> str:
        """
        获取 OAuth 授权 URL
        
        Args:
            state: 状态参数，用于防止 CSRF 攻击
        
        Returns:
            str: 授权 URL
        """
        config = cls.get_client_config()
        params = {
            'client_id': config['client_id'],
            'redirect_uri': config['redirect_uri'],
            'response_type': 'code',
        }
        if state:
            params['state'] = state

        # 子类可以覆盖此方法添加额外参数（如 scope）
        params.update(cls.get_extra_authorize_params())

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{cls.AUTHORIZE_URL}?{query_string}"

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """
        获取额外的授权参数（子类可覆盖）
        
        Returns:
            Dict: 额外参数
        """
        return {}

    @classmethod
    async def get_access_token(cls, code: str) -> Optional[str]:
        """
        使用授权码获取访问令牌
        
        Args:
            code: 授权码
        
        Returns:
            Optional[str]: 访问令牌，失败返回 None
        """
        try:
            config = cls.get_client_config()
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'redirect_uri': config['redirect_uri'],
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    cls.TOKEN_URL,
                    data=data,
                    headers=cls.get_token_request_headers(),
                )
                response.raise_for_status()

                result = response.json()
                access_token = result.get('access_token')

                if not access_token:
                    logger.error(f"获取 {cls.PROVIDER_NAME} access_token 失败: {result}")
                    return None

                return access_token

        except httpx.RequestError as e:
            logger.error(f"请求 {cls.PROVIDER_NAME} access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 {cls.PROVIDER_NAME} access_token 异常: {str(e)}")
            return None

    @classmethod
    def get_token_request_headers(cls) -> Dict[str, str]:
        """
        获取 token 请求的 headers（子类可覆盖）
        
        Returns:
            Dict: headers
        """
        return {}

    @classmethod
    @abstractmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取用户信息（子类必须实现）
        
        Args:
            access_token: 访问令牌
        
        Returns:
            Optional[Dict]: 用户信息字典，失败返回 None
        """
        pass

    @classmethod
    @abstractmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """
        标准化用户信息（子类必须实现）
        
        将不同 OAuth 提供商的用户信息格式统一为标准格式
        
        Args:
            raw_user_info: 原始用户信息
        
        Returns:
            Dict: 标准化后的用户信息，包含:
                - provider_id: 提供商的用户 ID
                - username: 用户名
                - name: 显示名称
                - email: 邮箱
                - avatar: 头像 URL
                - bio: 个人简介
        """
        pass

    @classmethod
    def get_user_id_field(cls) -> str:
        """
        获取用户 ID 字段名（如 gitee_id, github_id）
        
        Returns:
            str: 字段名
        """
        return f"{cls.PROVIDER_NAME}_id"

    @classmethod
    async def handle_oauth_login(
            cls,
            db: AsyncSession,
            code: str,
            ip_address: str,
            user_agent: str = None,
            login_type: str = None,
            device_id: str = None
    ) -> Tuple[User, str, str, int]:
        """
        处理 OAuth 登录流程
        
        Args:
            db: 数据库会话
            code: 授权码
            ip_address: 用户 IP 地址
            user_agent: 用户代理字符串
            login_type: 登录方式 (gitee/github/qq/google/wechat/microsoft)
            device_id: 设备标识（用于多设备登录）
        
        Returns:
            Tuple: (user, access_token, refresh_token, expire_time)
        
        Raises:
            ValueError: 登录失败时抛出
        """
        # 1. 使用 code 换取 access_token
        access_token = await cls.get_access_token(code)
        if not access_token:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 访问令牌失败")

        # 2. 使用 access_token 获取用户信息
        raw_user_info = await cls.get_user_info(access_token)
        if not raw_user_info:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 用户信息失败")

        # 3. 标准化用户信息
        user_info = cls.normalize_user_info(raw_user_info)
        provider_id = user_info['provider_id']
        username = user_info['username']
        name = user_info['name']
        email = user_info.get('email')
        avatar = user_info.get('avatar')
        bio = user_info.get('bio')

        # 4. 查找或创建用户
        user_id_field = cls.get_user_id_field()
        
        # 根据 provider_id 查找用户
        stmt = select(User).where(
            getattr(User, user_id_field) == provider_id,
            User.is_deleted == False
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        is_superadmin = getattr(settings, 'GRANT_ADMIN_TO_OAUTH_USER', False)
        default_dept_id = getattr(settings, 'OAUTH_DEFAULT_DEPT_ID', None)

        if user:
            # 用户已存在，更新信息
            logger.info(f"{cls.PROVIDER_NAME} 用户已存在: {username} (ID: {provider_id})")

            if email and not user.email:
                user.email = email
            if bio and not user.bio:
                user.bio = bio

            db.add(user)
            await db.flush()
        else:
            # 用户不存在，创建新用户
            logger.info(f"创建新的 {cls.PROVIDER_NAME} 用户: {username} (ID: {provider_id})")

            # 生成唯一的用户名
            unique_username = username
            counter = 1
            while True:
                stmt = select(User).where(User.username == unique_username)
                result = await db.execute(stmt)
                if result.scalar_one_or_none() is None:
                    break
                unique_username = f"{username}_{counter}"
                counter += 1

            # 创建用户
            create_kwargs = {
                'username': unique_username,
                'name': name,
                'email': email,
                'bio': bio,
                user_id_field: provider_id,
                'oauth_provider': cls.PROVIDER_NAME,
                'user_type': 1,  # 普通用户
                'user_status': 1,  # 正常状态
                'is_active': True,
                'is_superuser': is_superadmin,
                'dept_id': default_dept_id,
            }
            user = User(**create_kwargs)
            db.add(user)
            await db.flush()
            await db.refresh(user)
            logger.info(f"{cls.PROVIDER_NAME} 用户创建成功: {unique_username}")

        # 更新用户最后登录方式
        if login_type:
            user.last_login_type = login_type
            db.add(user)
            await db.flush()

        # 先提交用户数据，确保user.id可用
        await db.commit()
        await db.refresh(user)

        # 检查用户状态
        if not user.is_active:
            raise ValueError("账户已被禁用")

        if user.user_status == 0:
            raise ValueError("账户已被禁用")

        if user.user_status == 2:
            raise ValueError("账户已被锁定，请联系管理员")

        # 5. 生成 JWT token（token中只存身份标识，不存角色等动态信息）
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        token_data = {
            "sub": user.id,
            "username": user.username,
        }
        jwt_access_token = create_access_token(token_data, access_token_expires, device_id=device_id)
        jwt_refresh_token = create_refresh_token(token_data, refresh_token_expires, device_id=device_id)
        
        # 将用户动态信息缓存到 Redis
        from utils.user_info_cache import set_cached_user_info
        from core.user.service import UserService
        role_ids = await UserService.get_user_role_ids(db, user.id)
        await set_cached_user_info(user.id, role_ids, user.dept_id, user.is_superuser)
        expire_time = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # 将refresh token存入Redis
        redis = await RedisClient.get_client()
        
        # 如果不允许多设备登录，删除该用户的所有旧设备token
        if not settings.ALLOW_MULTI_DEVICE_LOGIN:
            # 查找并删除该用户的所有refresh token和access token
            refresh_pattern = f"{REFRESH_TOKEN_PREFIX}{user.id}:*"
            access_pattern = f"access_token:{user.id}:*"
            
            # 删除所有refresh token
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=refresh_pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
            
            # 删除所有access token
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=access_pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
        
        # 存储新的refresh token
        redis_key = f"{REFRESH_TOKEN_PREFIX}{user.id}:{device_id}" if device_id else f"{REFRESH_TOKEN_PREFIX}{user.id}"
        await redis.set(
            redis_key,
            jwt_refresh_token,
            ex=int(refresh_token_expires.total_seconds())
        )
        
        # 存储 access token（用于判断设备在线状态）
        if device_id:
            await redis.set(
                f"access_token:{user.id}:{device_id}",
                jwt_access_token,
                ex=int(access_token_expires.total_seconds())
            )

        # 6. 记录登录日志（record_login内部会commit）
        await LoginLogService.record_login(
            db=db,
            username=user.username,
            user_id=str(user.id),
            status=1,
            login_ip=ip_address,
            user_agent=user_agent,
            login_type=login_type or cls.PROVIDER_NAME,
        )

        return user, jwt_access_token, jwt_refresh_token, expire_time
