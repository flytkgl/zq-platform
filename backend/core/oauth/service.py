#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OAuth Service - OAuth 业务逻辑层
处理第三方 OAuth 登录逻辑（异步版本）
"""
import json
import logging
import re
from typing import Dict, Optional, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from core.oauth.base_oauth_service import BaseOAuthService
from core.user.model import User

logger = logging.getLogger(__name__)


class GiteeOAuthService(BaseOAuthService):
    """Gitee OAuth 服务类"""

    PROVIDER_NAME = 'gitee'
    AUTHORIZE_URL = "https://gitee.com/oauth/authorize"
    TOKEN_URL = "https://gitee.com/oauth/token"
    USER_INFO_URL = "https://gitee.com/api/v5/user"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 Gitee 客户端配置"""
        return {
            'client_id': getattr(settings, 'GITEE_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'GITEE_CLIENT_SECRET', ''),
            'redirect_uri': getattr(settings, 'GITEE_REDIRECT_URI', ''),
        }

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用访问令牌获取 Gitee 用户信息
        """
        try:
            params = {'access_token': access_token}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, params=params)
                response.raise_for_status()

                user_info = response.json()

                if 'id' not in user_info:
                    logger.error(f"Gitee 用户信息格式错误: {user_info}")
                    return None

                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求 Gitee 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 Gitee 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化 Gitee 用户信息"""
        return {
            'provider_id': str(raw_user_info.get('id')),
            'username': raw_user_info.get('login'),
            'name': raw_user_info.get('name', raw_user_info.get('login')),
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatar_url'),
            'bio': raw_user_info.get('bio'),
        }


class GitHubOAuthService(BaseOAuthService):
    """GitHub OAuth 服务类"""

    PROVIDER_NAME = 'github'
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 GitHub 客户端配置"""
        return {
            'client_id': getattr(settings, 'GITHUB_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'GITHUB_CLIENT_SECRET', ''),
            'redirect_uri': getattr(settings, 'GITHUB_REDIRECT_URI', ''),
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """GitHub 需要 scope 参数"""
        return {
            'scope': 'user:email',
        }

    @classmethod
    def get_token_request_headers(cls) -> Dict[str, str]:
        """GitHub 需要 Accept header 来获取 JSON 响应"""
        return {
            'Accept': 'application/json',
        }

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """使用访问令牌获取 GitHub 用户信息"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, headers=headers)
                response.raise_for_status()

                user_info = response.json()

                if 'id' not in user_info:
                    logger.error(f"GitHub 用户信息格式错误: {user_info}")
                    return None

                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求 GitHub 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 GitHub 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化 GitHub 用户信息"""
        return {
            'provider_id': str(raw_user_info.get('id')),
            'username': raw_user_info.get('login'),
            'name': raw_user_info.get('name') or raw_user_info.get('login'),
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatar_url'),
            'bio': raw_user_info.get('bio'),
        }


class QQOAuthService(BaseOAuthService):
    """QQ 互联 OAuth 服务类"""

    PROVIDER_NAME = 'qq'
    AUTHORIZE_URL = "https://graph.qq.com/oauth2.0/authorize"
    TOKEN_URL = "https://graph.qq.com/oauth2.0/token"
    USER_INFO_URL = "https://graph.qq.com/user/get_user_info"
    OPENID_URL = "https://graph.qq.com/oauth2.0/me"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 QQ 客户端配置"""
        return {
            'client_id': getattr(settings, 'QQ_APP_ID', ''),
            'client_secret': getattr(settings, 'QQ_APP_KEY', ''),
            'redirect_uri': getattr(settings, 'QQ_REDIRECT_URI', ''),
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """QQ 需要 response_type 参数"""
        return {
            'response_type': 'code',
        }

    @classmethod
    async def get_access_token(cls, code: str) -> Optional[str]:
        """使用授权码获取访问令牌（QQ 返回 URL 参数格式）"""
        try:
            config = cls.get_client_config()

            params = {
                'grant_type': 'authorization_code',
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code,
                'redirect_uri': config['redirect_uri'],
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.TOKEN_URL, params=params)
                response.raise_for_status()

                # QQ 返回的是 URL 参数格式: access_token=xxx&expires_in=xxx
                response_text = response.text

                match = re.search(r'access_token=([^&]+)', response_text)
                if match:
                    access_token = match.group(1)
                    logger.info(f"QQ access_token 获取成功")
                    return access_token
                else:
                    logger.error(f"QQ access_token 解析失败: {response_text}")
                    return None

        except httpx.RequestError as e:
            logger.error(f"请求 QQ access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 QQ access_token 异常: {str(e)}")
            return None

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """使用访问令牌获取 QQ 用户信息"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 1. 获取 openid
                openid_response = await client.get(
                    cls.OPENID_URL,
                    params={'access_token': access_token}
                )
                openid_response.raise_for_status()

                # QQ 返回的是 JSONP 格式: callback( {"client_id":"xxx","openid":"xxx"} );
                openid_text = openid_response.text

                match = re.search(r'callback\(\s*(\{.*?\})\s*\)', openid_text)
                if not match:
                    logger.error(f"QQ openid 解析失败: {openid_text}")
                    return None

                openid_data = json.loads(match.group(1))
                openid = openid_data.get('openid')

                if not openid:
                    logger.error(f"QQ openid 不存在: {openid_data}")
                    return None

                logger.info(f"QQ openid 获取成功: {openid}")

                # 2. 获取用户信息
                config = cls.get_client_config()
                user_response = await client.get(
                    cls.USER_INFO_URL,
                    params={
                        'access_token': access_token,
                        'oauth_consumer_key': config['client_id'],
                        'openid': openid
                    }
                )
                user_response.raise_for_status()

                user_info = user_response.json()

                if user_info.get('ret') != 0:
                    logger.error(f"QQ 用户信息获取失败: {user_info.get('msg')}")
                    return None

                user_info['openid'] = openid
                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求 QQ 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 QQ 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化 QQ 用户信息"""
        return {
            'provider_id': raw_user_info.get('openid'),
            'username': raw_user_info.get('nickname', '').replace(' ', '_'),
            'name': raw_user_info.get('nickname'),
            'email': None,
            'avatar': raw_user_info.get('figureurl_qq_2') or raw_user_info.get('figureurl_qq_1'),
            'bio': None,
        }


class GoogleOAuthService(BaseOAuthService):
    """Google OAuth 服务类"""

    PROVIDER_NAME = 'google'
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取 Google 客户端配置"""
        return {
            'client_id': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
            'redirect_uri': getattr(settings, 'GOOGLE_REDIRECT_URI', ''),
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """Google 需要 scope 和 access_type 参数"""
        return {
            'scope': 'openid email profile',
            'access_type': 'offline',
            'response_type': 'code',
        }

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """使用访问令牌获取 Google 用户信息"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, headers=headers)
                response.raise_for_status()

                user_info = response.json()

                if 'id' not in user_info:
                    logger.error(f"Google 用户信息格式错误: {user_info}")
                    return None

                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求 Google 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 Google 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化 Google 用户信息"""
        return {
            'provider_id': raw_user_info.get('id'),
            'username': raw_user_info.get('email', '').split('@')[0],
            'name': raw_user_info.get('name') or raw_user_info.get('email'),
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('picture'),
            'bio': None,
        }


class WeChatOAuthService(BaseOAuthService):
    """微信开放平台 OAuth 服务类"""

    PROVIDER_NAME = 'wechat'
    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
    USER_INFO_URL = "https://api.weixin.qq.com/sns/userinfo"

    @classmethod
    def get_user_id_field(cls) -> str:
        """微信使用 unionid 作为唯一标识"""
        return 'wechat_unionid'

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取微信客户端配置"""
        return {
            'client_id': getattr(settings, 'WECHAT_APP_ID', ''),
            'client_secret': getattr(settings, 'WECHAT_APP_SECRET', ''),
            'redirect_uri': getattr(settings, 'WECHAT_REDIRECT_URI', ''),
        }

    @classmethod
    def get_authorize_url(cls, state: str = None) -> str:
        """获取微信授权 URL（微信参数名称与标准 OAuth 2.0 不同）"""
        config = cls.get_client_config()

        params = {
            'appid': config['client_id'],
            'redirect_uri': config['redirect_uri'],
            'response_type': 'code',
            'scope': 'snsapi_login',
        }

        if state:
            params['state'] = state

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{cls.AUTHORIZE_URL}?{query_string}#wechat_redirect"

    @classmethod
    async def get_access_token(cls, code: str) -> Optional[Dict]:
        """使用授权码获取访问令牌（微信返回 access_token 和 openid）"""
        try:
            config = cls.get_client_config()
            params = {
                'appid': config['client_id'],
                'secret': config['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.TOKEN_URL, params=params)
                response.raise_for_status()

                token_data = response.json()

                if 'errcode' in token_data:
                    logger.error(f"微信获取 token 失败: {token_data}")
                    return None

                if 'access_token' not in token_data or 'openid' not in token_data:
                    logger.error(f"微信 token 响应格式错误: {token_data}")
                    return None

                return token_data

        except httpx.RequestError as e:
            logger.error(f"请求微信 token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取微信 token 异常: {str(e)}")
            return None

    @classmethod
    async def get_user_info(cls, access_token: str, openid: str = None) -> Optional[Dict]:
        """使用访问令牌获取微信用户信息"""
        try:
            params = {
                'access_token': access_token,
                'openid': openid,
                'lang': 'zh_CN',
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, params=params)
                response.raise_for_status()

                user_info = response.json()

                if 'errcode' in user_info:
                    logger.error(f"微信获取用户信息失败: {user_info}")
                    return None

                if 'openid' not in user_info:
                    logger.error(f"微信用户信息格式错误: {user_info}")
                    return None

                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求微信用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取微信用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化微信用户信息"""
        provider_id = raw_user_info.get('unionid') or raw_user_info.get('openid')
        nickname = raw_user_info.get('nickname', '')
        username = nickname.replace(' ', '_')[:30] if nickname else f"wechat_{provider_id[:8]}"

        return {
            'provider_id': provider_id,
            'username': username,
            'name': nickname or username,
            'email': None,
            'avatar': raw_user_info.get('headimgurl'),
            'bio': None,
        }

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
        处理微信 OAuth 登录流程（重写基类方法）
        
        微信的 get_access_token 返回 Dict（含 access_token 和 openid），
        且 get_user_info 需要同时传递 access_token 和 openid，
        因此需要重写此方法以正确处理。
        """
        # 1. 使用 code 换取 token_data（Dict，含 access_token + openid）
        token_data = await cls.get_access_token(code)
        if not token_data:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 访问令牌失败")

        access_token = token_data.get('access_token')
        openid = token_data.get('openid')

        if not access_token or not openid:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 访问令牌格式错误")

        # 2. 使用 access_token + openid 获取用户信息
        raw_user_info = await cls.get_user_info(access_token, openid=openid)
        if not raw_user_info:
            raise ValueError(f"获取 {cls.PROVIDER_NAME} 用户信息失败")

        # 3. 后续流程与基类一致，调用基类的通用逻辑
        #    先标准化用户信息，然后手动执行基类 handle_oauth_login 中第222行之后的逻辑
        #    为避免代码重复，将 access_token(str) 设置到类属性后调用基类
        #    但基类的 handle_oauth_login 会重新调用 get_access_token，所以这里直接复用基类的用户处理逻辑
        return await cls._handle_user_login(
            db=db,
            raw_user_info=raw_user_info,
            ip_address=ip_address,
            user_agent=user_agent,
            login_type=login_type,
            device_id=device_id,
        )

    @classmethod
    async def _handle_user_login(
            cls,
            db: AsyncSession,
            raw_user_info: Dict,
            ip_address: str,
            user_agent: str = None,
            login_type: str = None,
            device_id: str = None,
    ) -> Tuple[User, str, str, int]:
        """微信专用：从已获取的用户信息开始执行登录流程（复用基类逻辑）"""
        from datetime import timedelta
        from sqlalchemy import select
        from utils.redis import RedisClient
        from core.login_log.service import LoginLogService
        from utils.security import create_access_token, create_refresh_token
        from utils.user_info_cache import set_cached_user_info
        from core.user.service import UserService
        from core.oauth.base_oauth_service import REFRESH_TOKEN_PREFIX

        # 标准化用户信息
        user_info = cls.normalize_user_info(raw_user_info)
        provider_id = user_info['provider_id']
        username = user_info['username']
        name = user_info['name']
        email = user_info.get('email')
        avatar = user_info.get('avatar')
        bio = user_info.get('bio')

        # 查找或创建用户
        user_id_field = cls.get_user_id_field()
        stmt = select(User).where(
            getattr(User, user_id_field) == provider_id,
            User.is_deleted == False
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        is_superadmin = getattr(settings, 'GRANT_ADMIN_TO_OAUTH_USER', False)
        default_dept_id = getattr(settings, 'OAUTH_DEFAULT_DEPT_ID', None)

        if user:
            logger.info(f"{cls.PROVIDER_NAME} 用户已存在: {username} (ID: {provider_id})")
            if email and not user.email:
                user.email = email
            if bio and not user.bio:
                user.bio = bio
            db.add(user)
            await db.flush()
        else:
            logger.info(f"创建新的 {cls.PROVIDER_NAME} 用户: {username} (ID: {provider_id})")
            unique_username = username
            counter = 1
            while True:
                stmt = select(User).where(User.username == unique_username)
                result = await db.execute(stmt)
                if result.scalar_one_or_none() is None:
                    break
                unique_username = f"{username}_{counter}"
                counter += 1

            create_kwargs = {
                'username': unique_username,
                'name': name,
                'email': email,
                'bio': bio,
                user_id_field: provider_id,
                'oauth_provider': cls.PROVIDER_NAME,
                'user_type': 1,
                'user_status': 1,
                'is_active': True,
                'is_superuser': is_superadmin,
                'dept_id': default_dept_id,
            }
            user = User(**create_kwargs)
            db.add(user)
            await db.flush()
            await db.refresh(user)
            logger.info(f"{cls.PROVIDER_NAME} 用户创建成功: {unique_username}")

        if login_type:
            user.last_login_type = login_type
            db.add(user)
            await db.flush()

        await db.commit()
        await db.refresh(user)

        if not user.is_active:
            raise ValueError("账户已被禁用")
        if user.user_status == 0:
            raise ValueError("账户已被禁用")
        if user.user_status == 2:
            raise ValueError("账户已被锁定，请联系管理员")

        # 生成 JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token_data = {"sub": user.id, "username": user.username}
        jwt_access_token = create_access_token(token_data, access_token_expires, device_id=device_id)
        jwt_refresh_token = create_refresh_token(token_data, refresh_token_expires, device_id=device_id)

        # 缓存用户信息到 Redis
        role_ids = await UserService.get_user_role_ids(db, user.id)
        await set_cached_user_info(user.id, role_ids, user.dept_id, user.is_superuser)
        expire_time = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        redis = await RedisClient.get_client()

        if not settings.ALLOW_MULTI_DEVICE_LOGIN:
            refresh_pattern = f"{REFRESH_TOKEN_PREFIX}{user.id}:*"
            access_pattern = f"access_token:{user.id}:*"
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=refresh_pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=access_pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break

        redis_key = f"{REFRESH_TOKEN_PREFIX}{user.id}:{device_id}" if device_id else f"{REFRESH_TOKEN_PREFIX}{user.id}"
        await redis.set(redis_key, jwt_refresh_token, ex=int(refresh_token_expires.total_seconds()))

        if device_id:
            await redis.set(
                f"access_token:{user.id}:{device_id}",
                jwt_access_token,
                ex=int(access_token_expires.total_seconds())
            )

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


class MicrosoftOAuthService(BaseOAuthService):
    """微软 OAuth 服务类"""

    PROVIDER_NAME = 'microsoft'
    AUTHORIZE_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取微软客户端配置"""
        return {
            'client_id': getattr(settings, 'MICROSOFT_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'MICROSOFT_CLIENT_SECRET', ''),
            'redirect_uri': getattr(settings, 'MICROSOFT_REDIRECT_URI', ''),
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """微软需要 scope 和 response_mode 参数"""
        return {
            'scope': 'openid email profile User.Read',
            'response_type': 'code',
            'response_mode': 'query',
        }

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """使用 Microsoft Graph API 获取用户信息"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, headers=headers)
                response.raise_for_status()

                user_info = response.json()

                if 'id' not in user_info:
                    logger.error(f"Microsoft 用户信息格式错误: {user_info}")
                    return None

                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求 Microsoft 用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取 Microsoft 用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化微软用户信息"""
        user_principal_name = raw_user_info.get('userPrincipalName', '')
        username = user_principal_name.split('@')[0] if '@' in user_principal_name else user_principal_name
        email = raw_user_info.get('mail') or raw_user_info.get('userPrincipalName')

        return {
            'provider_id': raw_user_info.get('id'),
            'username': username or f"ms_{raw_user_info.get('id', '')[:8]}",
            'name': raw_user_info.get('displayName') or username,
            'email': email,
            'avatar': None,
            'bio': raw_user_info.get('jobTitle'),
        }


class DingTalkOAuthService(BaseOAuthService):
    """钉钉 OAuth 服务类"""

    PROVIDER_NAME = 'dingtalk'
    AUTHORIZE_URL = "https://login.dingtalk.com/oauth2/auth"
    TOKEN_URL = "https://api.dingtalk.com/v1.0/oauth2/userAccessToken"
    USER_INFO_URL = "https://api.dingtalk.com/v1.0/contact/users/me"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取钉钉客户端配置"""
        return {
            'client_id': getattr(settings, 'DINGTALK_APP_ID', ''),
            'client_secret': getattr(settings, 'DINGTALK_APP_SECRET', ''),
            'redirect_uri': getattr(settings, 'DINGTALK_REDIRECT_URI', ''),
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """钉钉需要的额外授权参数"""
        return {
            'response_type': 'code',
            'scope': 'openid',
            'prompt': 'consent',
        }

    @classmethod
    async def get_access_token(cls, code: str) -> Optional[str]:
        """使用授权码获取访问令牌（钉钉使用 JSON body）"""
        try:
            config = cls.get_client_config()

            data = {
                'clientId': config['client_id'],
                'clientSecret': config['client_secret'],
                'code': code,
                'grantType': 'authorization_code',
            }

            headers = {
                'Content-Type': 'application/json',
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(cls.TOKEN_URL, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                if 'accessToken' in result:
                    logger.info(f"钉钉 access_token 获取成功")
                    return result['accessToken']
                else:
                    logger.error(f"钉钉 token 响应格式错误: {result}")
                    return None

        except httpx.RequestError as e:
            logger.error(f"请求钉钉 access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取钉钉 access_token 异常: {str(e)}")
            return None

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """使用访问令牌获取钉钉用户信息"""
        try:
            headers = {
                'x-acs-dingtalk-access-token': access_token,
                'Content-Type': 'application/json',
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, headers=headers)
                response.raise_for_status()

                user_info = response.json()

                if 'unionId' not in user_info:
                    logger.error(f"钉钉用户信息格式错误: {user_info}")
                    return None

                return user_info

        except httpx.RequestError as e:
            logger.error(f"请求钉钉用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取钉钉用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化钉钉用户信息"""
        provider_id = raw_user_info.get('unionId', '')
        nick = raw_user_info.get('nick', '')
        username = nick if nick else f"dingtalk_{provider_id[:8]}"

        return {
            'provider_id': provider_id,
            'username': username,
            'name': nick or username,
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatarUrl'),
            'mobile': raw_user_info.get('mobile'),
            'bio': f"钉钉用户 - {nick}" if nick else "钉钉用户",
        }

    @classmethod
    def get_user_id_field(cls) -> str:
        """获取用户 ID 字段名"""
        return 'dingtalk_unionid'


class FeishuOAuthService(BaseOAuthService):
    """飞书 OAuth 服务类"""

    PROVIDER_NAME = 'feishu'
    AUTHORIZE_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
    TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
    USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取飞书客户端配置"""
        return {
            'client_id': getattr(settings, 'FEISHU_APP_ID', ''),
            'client_secret': getattr(settings, 'FEISHU_APP_SECRET', ''),
            'redirect_uri': getattr(settings, 'FEISHU_REDIRECT_URI', ''),
        }

    @classmethod
    def get_extra_authorize_params(cls) -> Dict[str, str]:
        """飞书需要的额外授权参数"""
        return {
            'response_type': 'code',
            'scope': 'contact:user.base:readonly',
        }

    @classmethod
    async def _get_app_access_token(cls) -> Optional[str]:
        """获取应用级别的 access_token"""
        try:
            config = cls.get_client_config()

            url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
            data = {
                'app_id': config['client_id'],
                'app_secret': config['client_secret'],
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()

                result = response.json()

                if result.get('code') == 0:
                    return result.get('app_access_token')

                logger.error(f"获取飞书 app_access_token 失败: {result}")
                return None

        except Exception as e:
            logger.error(f"获取飞书 app_access_token 异常: {str(e)}")
            return None

    @classmethod
    async def get_access_token(cls, code: str) -> Optional[str]:
        """使用授权码获取访问令牌"""
        try:
            app_access_token = await cls._get_app_access_token()
            if not app_access_token:
                return None

            data = {
                'grant_type': 'authorization_code',
                'code': code,
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {app_access_token}',
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(cls.TOKEN_URL, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()

                if result.get('code') == 0 and 'data' in result:
                    access_token = result['data'].get('access_token')
                    if access_token:
                        logger.info(f"飞书 access_token 获取成功")
                        return access_token

                logger.error(f"飞书 token 响应格式错误: {result}")
                return None

        except httpx.RequestError as e:
            logger.error(f"请求飞书 access_token 失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取飞书 access_token 异常: {str(e)}")
            return None

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """使用访问令牌获取飞书用户信息"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, headers=headers)
                response.raise_for_status()

                result = response.json()

                if result.get('code') == 0 and 'data' in result:
                    user_info = result['data']
                    if 'union_id' not in user_info:
                        logger.error(f"飞书用户信息格式错误: {result}")
                        return None
                    return user_info

                logger.error(f"飞书用户信息响应错误: {result}")
                return None

        except httpx.RequestError as e:
            logger.error(f"请求飞书用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取飞书用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化飞书用户信息"""
        provider_id = raw_user_info.get('union_id', '')
        name = raw_user_info.get('name', '')
        en_name = raw_user_info.get('en_name', '')
        username = en_name or name or f"feishu_{provider_id[:8]}"
        username = username.replace(' ', '_')

        mobile = raw_user_info.get('mobile', '')
        if mobile and mobile.startswith('+86-'):
            mobile = mobile[4:]

        return {
            'provider_id': provider_id,
            'username': username,
            'name': name or username,
            'email': raw_user_info.get('email'),
            'avatar': raw_user_info.get('avatar_url') or raw_user_info.get('avatar_big'),
            'mobile': mobile,
            'bio': f"飞书用户 - {name}" if name else "飞书用户",
        }

    @classmethod
    def get_user_id_field(cls) -> str:
        """获取用户 ID 字段名"""
        return 'feishu_union_id'


class WeComOAuthService(BaseOAuthService):
    """企业微信 OAuth 服务类"""

    PROVIDER_NAME = 'wecom'
    AUTHORIZE_URL = "https://login.work.weixin.qq.com/wwlogin/sso/login"
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    USER_INFO_URL = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"
    USER_DETAIL_URL = "https://qyapi.weixin.qq.com/cgi-bin/user/get"

    @classmethod
    def get_user_id_field(cls) -> str:
        """企业微信使用 wecom_userid 作为唯一标识"""
        return 'wecom_userid'

    @classmethod
    def get_client_config(cls) -> Dict[str, str]:
        """获取企业微信客户端配置"""
        return {
            'client_id': getattr(settings, 'WECOM_CORP_ID', ''),
            'client_secret': getattr(settings, 'WECOM_APP_SECRET', ''),
            'redirect_uri': getattr(settings, 'WECOM_REDIRECT_URI', ''),
            'agent_id': getattr(settings, 'WECOM_AGENT_ID', ''),
        }

    @classmethod
    def get_authorize_url(cls, state: str = None) -> str:
        """获取企业微信授权 URL（企业微信使用特殊的 SSO 登录页面）"""
        config = cls.get_client_config()

        params = {
            'login_type': 'CorpApp',
            'appid': config['client_id'],
            'agentid': config['agent_id'],
            'redirect_uri': config['redirect_uri'],
        }

        if state:
            params['state'] = state

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{cls.AUTHORIZE_URL}?{query_string}"

    @classmethod
    async def _get_corp_access_token(cls) -> Optional[str]:
        """获取企业微信的企业级 access_token"""
        try:
            config = cls.get_client_config()
            params = {
                'corpid': config['client_id'],
                'corpsecret': config['client_secret'],
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.TOKEN_URL, params=params)
                response.raise_for_status()

                result = response.json()

                if result.get('errcode') == 0 and 'access_token' in result:
                    logger.info("企业微信 corp access_token 获取成功")
                    return result['access_token']

                logger.error(f"获取企业微信 corp access_token 失败: {result}")
                return None

        except Exception as e:
            logger.error(f"获取企业微信 corp access_token 异常: {str(e)}")
            return None

    @classmethod
    async def get_access_token(cls, code: str) -> Optional[str]:
        """
        企业微信不使用标准的 code 换 token 流程。
        这里获取 corp access_token 并返回，code 在 get_user_info 中使用。
        返回格式: "corp_access_token|code" 以便后续使用。
        """
        corp_token = await cls._get_corp_access_token()
        if not corp_token:
            return None
        # 将 corp_token 和 code 拼接传递，在 get_user_info 中拆分使用
        return f"{corp_token}|{code}"

    @classmethod
    async def get_user_info(cls, access_token: str) -> Optional[Dict]:
        """
        使用 corp access_token + code 获取企业微信用户信息。
        access_token 格式: "corp_access_token|code"
        """
        try:
            parts = access_token.split('|', 1)
            if len(parts) != 2:
                logger.error("企业微信 access_token 格式错误")
                return None

            corp_token, code = parts

            # 第一步：用 code 获取 userid
            params = {
                'access_token': corp_token,
                'code': code,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.USER_INFO_URL, params=params)
                response.raise_for_status()

                result = response.json()

                if result.get('errcode') != 0:
                    logger.error(f"企业微信获取用户身份失败: {result}")
                    return None

                userid = result.get('userid') or result.get('UserId')
                if not userid:
                    logger.error(f"企业微信用户身份响应中无 userid: {result}")
                    return None

                # 第二步：用 userid 获取用户详情
                detail_params = {
                    'access_token': corp_token,
                    'userid': userid,
                }

                detail_response = await client.get(cls.USER_DETAIL_URL, params=detail_params)
                detail_response.raise_for_status()

                user_detail = detail_response.json()

                if user_detail.get('errcode') != 0:
                    logger.error(f"企业微信获取用户详情失败: {user_detail}")
                    # 即使获取详情失败，也返回基本信息
                    return {
                        'userid': userid,
                        'name': userid,
                    }

                return user_detail

        except httpx.RequestError as e:
            logger.error(f"请求企业微信用户信息失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取企业微信用户信息异常: {str(e)}")
            return None

    @classmethod
    def normalize_user_info(cls, raw_user_info: Dict) -> Dict:
        """标准化企业微信用户信息"""
        userid = raw_user_info.get('userid', '')
        name = raw_user_info.get('name', '')
        username = userid if userid else f"wecom_{name}"

        email = raw_user_info.get('biz_mail') or raw_user_info.get('email')
        avatar = raw_user_info.get('thumb_avatar') or raw_user_info.get('avatar')
        mobile = raw_user_info.get('mobile', '')
        position = raw_user_info.get('position', '')

        return {
            'provider_id': userid,
            'username': username,
            'name': name or username,
            'email': email,
            'avatar': avatar,
            'bio': f"企业微信用户 - {position}" if position else "企业微信用户",
        }


# OAuth 提供商映射
OAUTH_PROVIDERS = {
    'gitee': GiteeOAuthService,
    'github': GitHubOAuthService,
    'qq': QQOAuthService,
    'google': GoogleOAuthService,
    'wechat': WeChatOAuthService,
    'microsoft': MicrosoftOAuthService,
    'dingtalk': DingTalkOAuthService,
    'feishu': FeishuOAuthService,
    'wecom': WeComOAuthService,
}
