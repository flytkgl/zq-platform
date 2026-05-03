#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auth Middleware - 全局认证和鉴权中间件

功能：
1. 认证（Authentication）：验证JWT Token的有效性
2. 鉴权（Authorization）：基于API路径的动态权限检查
"""
from typing import List, Optional, Callable
import re

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.security import verify_access_token
from utils.context import set_current_user_context, clear_current_user_context


# 默认白名单路由（不需要认证）
DEFAULT_WHITE_LIST = [
    # 认证相关
    "/api/core/login",
    "/api/core/refresh_token",
    # 文档相关
    "/docs",
    "/redoc",
    "/openapi.json",
    # 健康检查
    "/",
    "/health",
    # UI配置（前端初始化时需要无认证访问）
    "/api/core/ui_config/preferences",
]

# OAuth白名单正则模式
OAUTH_WHITE_LIST_PATTERNS = [
    r"^/api/core/oauth/.*/authorize$",   # OAuth授权URL获取
    r"^/api/core/oauth/.*/callback$",    # OAuth回调处理
]

# WebSocket白名单正则模式（WebSocket自己处理Token认证）
WEBSOCKET_WHITE_LIST_PATTERNS = [
    r"^/ws/.*",  # 所有WebSocket路径
]

# 白名单正则模式（支持通配符）
DEFAULT_WHITE_LIST_PATTERNS = [
    r"^/docs.*",
    r"^/redoc.*",
    r"^/api/core/applications/code/.*",  # 根据编码获取应用（子应用初始化需要）
    r"^/api/core/file_manager/stream/.*",
    r"^/api/core/file_manager/signature/info/.*",     # 签名令牌信息（移动端无需登录）
    r"^/api/core/file_manager/signature/upload/.*",   # 上传签名图片（移动端无需登录，需验证令牌）
    r"^/api/core/file_manager/signature/complete/.*", # 完成签名（移动端无需登录）
    r"^/api/core/contract/mobile/.*",                 # 合同移动端签署（无需登录）
    r"^/api/core/dingtalk-sync/callback$",             # 钉钉事件回调（钉钉服务器推送，无需登录）
    r"^/api/core/wecom-sync/callback$",                # 企业微信事件回调（企业微信服务器推送，无需登录）
    r"^/api/core/feishu-sync/callback$",               # 飞书事件回调（飞书服务器推送，无需登录）
    *OAUTH_WHITE_LIST_PATTERNS,  # OAuth相关接口
    *WEBSOCKET_WHITE_LIST_PATTERNS,  # WebSocket相关接口
]

# 允许使用Query参数传递Token的API路径模式（出于安全考虑，仅限特定接口）
# 主要用于文件下载、流式传输等无法设置Header的场景
QUERY_TOKEN_ALLOWED_PATTERNS = [
    r"^/api/core/file_manager/proxy/.*",       # 文件代理访问
    r"^/api/core/file_manager/file/download.*", # 文件下载
]

# 鉴权白名单（不需要权限检查，但需要认证）
DEFAULT_PERMISSION_WHITE_LIST = [
    "/api/core/userinfo",           # 获取当前用户信息
    "/api/core/logout",             # 登出
    "/api/core/user/change-password",    # 修改密码
]

# 鉴权白名单正则模式
DEFAULT_PERMISSION_WHITE_LIST_PATTERNS = [
    r"^/api/core/dict/type/.*/data$",  # 字典数据查询（所有登录用户都可以访问）
]


class AuthPermissionMiddleware(BaseHTTPMiddleware):
    """
    全局认证和鉴权中间件
    
    功能：
    - 认证：验证JWT Token的有效性
    - 鉴权：基于API路径的动态权限检查
    
    工作流程：
    1. 检查是否在白名单中，是则直接放行
    2. 验证JWT Token，获取用户信息
    3. 根据请求的API路径和方法，查找Permission表中是否有对应的权限记录
    4. 如果有权限记录，检查用户的角色是否关联了该权限
    5. 如果用户角色有该权限，则放行；否则返回403
    6. 如果Permission表中没有该API的权限记录，则默认放行
    """
    
    def __init__(
        self,
        app,
        white_list: Optional[List[str]] = None,
        white_list_patterns: Optional[List[str]] = None,
        permission_white_list: Optional[List[str]] = None,
        permission_white_list_patterns: Optional[List[str]] = None,
        enable_permission_check: bool = True,
    ):
        """
        初始化中间件
        
        :param app: FastAPI应用
        :param white_list: 认证白名单路由列表（精确匹配，不需要认证）
        :param white_list_patterns: 认证白名单正则模式列表（不需要认证）
        :param permission_white_list: 鉴权白名单路由列表（需要认证，但不需要权限检查）
        :param permission_white_list_patterns: 鉴权白名单正则模式列表（需要认证，但不需要权限检查）
        :param enable_permission_check: 是否启用权限检查（默认True）
        """
        super().__init__(app)
        self.white_list = set(white_list or DEFAULT_WHITE_LIST)
        self.white_list_patterns = [
            re.compile(p) for p in (white_list_patterns or DEFAULT_WHITE_LIST_PATTERNS)
        ]
        self.permission_white_list = set(permission_white_list or DEFAULT_PERMISSION_WHITE_LIST)
        self.permission_white_list_patterns = [
            re.compile(p) for p in (permission_white_list_patterns or DEFAULT_PERMISSION_WHITE_LIST_PATTERNS)
        ]
        self.enable_permission_check = enable_permission_check
    
    def is_white_listed(self, path: str) -> bool:
        """
        检查路径是否在白名单中（不需要认证）
        
        :param path: 请求路径
        :return: 是否在白名单中
        """
        # 精确匹配
        if path in self.white_list:
            return True
        
        # 正则匹配
        for pattern in self.white_list_patterns:
            if pattern.match(path):
                return True
        
        return False
    
    def is_permission_white_listed(self, path: str) -> bool:
        """
        检查路径是否在鉴权白名单中（需要认证，但不需要权限检查）
        
        :param path: 请求路径
        :return: 是否在鉴权白名单中
        """
        # 精确匹配
        if path in self.permission_white_list:
            return True
        
        # 正则匹配
        for pattern in self.permission_white_list_patterns:
            if pattern.match(path):
                return True
        
        return False
    
    def _is_query_token_allowed(self, path: str) -> bool:
        """
        检查路径是否允许使用Query参数传递Token
        
        出于安全考虑，仅允许特定接口使用Query Token
        """
        for pattern in [re.compile(p) for p in QUERY_TOKEN_ALLOWED_PATTERNS]:
            if pattern.match(path):
                return True
        return False

    def _extract_token(self, request: Request) -> str | None:
        """
        从请求中提取Token
        
        支持两种方式：
        1. Authorization Header: Bearer <token>（所有接口）
        2. Query参数: ?token=<token>（仅限特定接口，如文件下载）
        """
        # 优先从Authorization头获取
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                return parts[1]
        
        # Query参数方式仅限特定接口
        path = request.url.path
        if self._is_query_token_allowed(path):
            token = request.query_params.get("token")
            if token:
                return token
        
        return None
    
    async def _verify_api_token(self, raw_token: str):
        """
        验证 API Token (Personal Access Token)
        
        :return: (user_id, username) 或 (None, None)
        """
        from app.database import AsyncSessionLocal
        from core.api_token.service import ApiTokenService
        
        async with AsyncSessionLocal() as db:
            token_record = await ApiTokenService.verify_token(db, raw_token)
            if not token_record:
                return None, None
            
            from core.user.service import UserService
            user = await UserService.get_by_id(db, token_record.user_id)
            if not user or not user.is_active:
                return None, None
            
            return user.id, user.username
    
    async def dispatch(self, request: Request, call_next: Callable):
        """处理请求"""
        path = request.url.path
        method = request.method
        
        # 白名单路由直接放行
        if self.is_white_listed(path):
            return await call_next(request)
        
        # OPTIONS请求放行（CORS预检）
        if method == "OPTIONS":
            return await call_next(request)
        
        # ========== 认证（Authentication）==========
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "未提供认证凭据"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查是否为 API Token (Personal Access Token)
        is_api_token = token.startswith("zqpat_")
        user_id = None
        username = None
        
        if is_api_token:
            try:
                user_id, username = await self._verify_api_token(token)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("API Token验证异常")
                user_id, username = None, None
            if not user_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "无效或过期的API Token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            payload = verify_access_token(token)
            if not payload:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "无效或过期的Token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 检查 access token 是否在 Redis 白名单中（防止已登出的token被使用）
            user_id = payload.get("sub")
            device_id = payload.get("device_id")
            username = payload.get("username")
            
            if user_id and device_id:
                from utils.redis import RedisClient
                redis = await RedisClient.get_client()
                access_token_key = f"access_token:{user_id}:{device_id}"
                token_exists = await redis.exists(access_token_key)
                
                if not token_exists:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Token已失效，请重新登录"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        
        # 从 Redis 缓存获取用户动态信息（角色、部门、超管等）
        from utils.user_info_cache import get_cached_user_info, load_user_info_from_db
        
        user_info = await get_cached_user_info(user_id)
        if not user_info:
            user_info = await load_user_info_from_db(user_id)
        
        if not user_info:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "用户不存在"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not username:
            username = user_info.get("username")
        
        role_ids = user_info.get("role_ids", [])
        role_id = role_ids[0] if role_ids else None
        dept_id = user_info.get("dept_id")
        is_superuser = user_info.get("is_superuser", False)
        
        # 将用户信息存入request.state
        request.state.user_id = user_id
        request.state.username = username
        request.state.role_id = role_id
        request.state.role_ids = role_ids
        request.state.dept_id = dept_id
        request.state.is_superuser = is_superuser
        request.state.token_payload = {} if is_api_token else payload
        
        # 设置完整用户信息和请求信息到上下文（供Service层使用）
        set_current_user_context(
            user_id=user_id,
            role_id=role_id,
            role_ids=role_ids,
            dept_id=dept_id,
            is_superuser=is_superuser,
            username=username,
            request_path=path,
            http_method=method
        )
        
        try:
            # ========== 鉴权（Authorization）==========
            if self.enable_permission_check:
                # 检查是否在鉴权白名单中
                if self.is_permission_white_listed(path):
                    # 在鉴权白名单中，跳过权限检查
                    pass
                # 超级管理员跳过权限检查
                elif is_superuser:
                    pass
                else:
                    # 普通用户需要进行权限检查
                    from app.database import AsyncSessionLocal
                    from utils.permission import check_api_permission
                    
                    async with AsyncSessionLocal() as db:
                        has_permission, error_msg = await check_api_permission(
                            db=db,
                            user_id=user_id,
                            role_ids=role_ids,
                            is_superuser=is_superuser,
                            request_path=path,
                            http_method=method,
                        )
                        
                        if not has_permission:
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={"detail": error_msg or "权限不足"},
                            )
            
            response = await call_next(request)
            return response
        finally:
            # 请求结束后清除上下文
            clear_current_user_context()


def get_auth_middleware(
    white_list: Optional[List[str]] = None,
    white_list_patterns: Optional[List[str]] = None,
    permission_white_list: Optional[List[str]] = None,
    permission_white_list_patterns: Optional[List[str]] = None,
) -> type:
    """
    获取配置好的认证+鉴权中间件类
    
    使用方式：
    app.add_middleware(get_auth_middleware(
        white_list=["/public"],  # 不需要认证的接口
        permission_white_list=["/api/my/profile"]  # 需要认证但不需要权限检查的接口
    ))
    
    :param white_list: 额外的认证白名单路由（不需要认证）
    :param white_list_patterns: 额外的认证白名单正则模式（不需要认证）
    :param permission_white_list: 额外的鉴权白名单路由（需要认证，但不需要权限检查）
    :param permission_white_list_patterns: 额外的鉴权白名单正则模式（需要认证，但不需要权限检查）
    :return: 配置好的中间件类
    """
    merged_white_list = list(DEFAULT_WHITE_LIST)
    if white_list:
        merged_white_list.extend(white_list)
    
    merged_patterns = list(DEFAULT_WHITE_LIST_PATTERNS)
    if white_list_patterns:
        merged_patterns.extend(white_list_patterns)
    
    merged_permission_white_list = list(DEFAULT_PERMISSION_WHITE_LIST)
    if permission_white_list:
        merged_permission_white_list.extend(permission_white_list)
    
    merged_permission_patterns = list(DEFAULT_PERMISSION_WHITE_LIST_PATTERNS)
    if permission_white_list_patterns:
        merged_permission_patterns.extend(permission_white_list_patterns)
    
    class ConfiguredMiddleware(AuthPermissionMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                white_list=merged_white_list,
                white_list_patterns=merged_patterns,
                permission_white_list=merged_permission_white_list,
                permission_white_list_patterns=merged_permission_patterns,
                enable_permission_check=True,
            )
    
    return ConfiguredMiddleware


def get_auth_permission_middleware(
    white_list: Optional[List[str]] = None,
    white_list_patterns: Optional[List[str]] = None,
    permission_white_list: Optional[List[str]] = None,
    permission_white_list_patterns: Optional[List[str]] = None,
) -> type:
    """
    获取配置好的认证+鉴权中间件类（别名函数，与 get_auth_middleware 相同）
    
    使用方式：
    app.add_middleware(get_auth_permission_middleware(
        white_list=["/public"],  # 不需要认证的接口
        permission_white_list=["/api/my/profile"]  # 需要认证但不需要权限检查的接口
    ))
    
    :param white_list: 额外的认证白名单路由（不需要认证）
    :param white_list_patterns: 额外的认证白名单正则模式（不需要认证）
    :param permission_white_list: 额外的鉴权白名单路由（需要认证，但不需要权限检查）
    :param permission_white_list_patterns: 额外的鉴权白名单正则模式（需要认证，但不需要权限检查）
    :return: 配置好的中间件类
    """
    return get_auth_middleware(
        white_list=white_list,
        white_list_patterns=white_list_patterns,
        permission_white_list=permission_white_list,
        permission_white_list_patterns=permission_white_list_patterns,
    )
