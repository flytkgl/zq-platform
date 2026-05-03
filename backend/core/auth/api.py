#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auth API - 认证相关接口
"""
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.base_schema import ResponseModel
from utils.redis import RedisClient
from core.auth.schema import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LoginUserInfo,
)
from core.user.service import UserService
from core.login_log.service import LoginLogService
from utils.client_info import get_client_info, get_device_id
from utils.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user,
)

router = APIRouter(prefix="", tags=["认证管理"])

# Redis中存储refresh token的key前缀
REFRESH_TOKEN_PREFIX = "refresh_token:"
# Redis中存储token黑名单的key前缀
TOKEN_BLACKLIST_PREFIX = "token_blacklist:"


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录（JSON格式，供前端使用）
    
    - **username**: 用户名
    - **password**: 密码
    
    返回access_token和refresh_token
    """
    # 获取客户端信息和设备标识
    client_info = get_client_info(request)
    device_id = get_device_id(request)
    
    # 验证用户
    user = await UserService.authenticate(db, data.username, data.password)
    if not user:
        # 记录登录失败日志
        await LoginLogService.record_login(
            db=db,
            username=data.username,
            status=0,
            login_ip=client_info["login_ip"],
            failure_reason=2,  # 密码错误
            failure_message="用户名或密码错误",
            user_agent=client_info["user_agent"],
            browser_type=client_info["browser_type"],
            os_type=client_info["os_type"],
            device_type=client_info["device_type"],
            login_type="password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        # 记录登录失败日志
        await LoginLogService.record_login(
            db=db,
            username=data.username,
            user_id=user.id,
            status=0,
            login_ip=client_info["login_ip"],
            failure_reason=3,  # 用户已禁用
            failure_message="用户已被禁用",
            user_agent=client_info["user_agent"],
            browser_type=client_info["browser_type"],
            os_type=client_info["os_type"],
            device_type=client_info["device_type"],
            login_type="password",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    if user.user_status != 1:
        status_msg = {0: "用户已禁用", 2: "用户已锁定"}.get(user.user_status, "用户状态异常")
        failure_reason = 3 if user.user_status == 0 else 4  # 3=禁用, 4=锁定
        # 记录登录失败日志
        await LoginLogService.record_login(
            db=db,
            username=data.username,
            user_id=user.id,
            status=0,
            login_ip=client_info["login_ip"],
            failure_reason=failure_reason,
            failure_message=status_msg,
            user_agent=client_info["user_agent"],
            browser_type=client_info["browser_type"],
            os_type=client_info["os_type"],
            device_type=client_info["device_type"],
            login_type="password",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=status_msg
        )
    
    # 生成token（token中只存身份标识，不存角色等动态信息）
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {
        "sub": user.id,
        "username": user.username,
    }
    access_token = create_access_token(token_data, access_token_expires, device_id=device_id)
    refresh_token = create_refresh_token(token_data, refresh_token_expires, device_id=device_id)
    
    # 将用户动态信息缓存到 Redis（中间件从此处获取角色等信息）
    from utils.user_info_cache import set_cached_user_info
    role_ids = await UserService.get_user_role_ids(db, user.id)
    await set_cached_user_info(user.id, role_ids, user.dept_id, user.is_superuser)
    
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
    await redis.set(
        f"{REFRESH_TOKEN_PREFIX}{user.id}:{device_id}",
        refresh_token,
        ex=int(refresh_token_expires.total_seconds())
    )
    
    # 存储 access token（用于判断设备在线状态）
    await redis.set(
        f"access_token:{user.id}:{device_id}",
        access_token,
        ex=int(access_token_expires.total_seconds())
    )
    
    # 存储设备信息
    device_info_key = f"device_info:{user.id}:{device_id}"
    await redis.hset(device_info_key, mapping={
        "device_type": client_info["device_type"],
        "browser_type": client_info["browser_type"] or "Unknown",
        "os_type": client_info["os_type"] or "Unknown",
        "ip_address": client_info["login_ip"],
        "last_active_time": datetime.now(timezone.utc).isoformat()
    })
    await redis.expire(device_info_key, int(refresh_token_expires.total_seconds()))
    
    # 更新最后登录时间和IP
    await UserService.update_login_info(db, user.id, login_type="password")
    
    # 记录登录成功日志
    await LoginLogService.record_login(
        db=db,
        username=user.username,
        user_id=user.id,
        status=1,
        login_ip=client_info["login_ip"],
        user_agent=client_info["user_agent"],
        browser_type=client_info["browser_type"],
        os_type=client_info["os_type"],
        device_type=client_info["device_type"],
        login_type="password",
    )
    
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        expireTime=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login/oauth2", response_model=TokenResponse, summary="OAuth2登录(OAuth2)", include_in_schema=True)
async def login_oauth2(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录（OAuth2表单格式，供Swagger使用）
    
    - **username**: 用户名
    - **password**: 密码
    
    返回access_token和refresh_token（标准OAuth2格式）
    """
    # 获取客户端信息和设备标识
    client_info = get_client_info(request)
    device_id = get_device_id(request)
    
    # 验证用户
    user = await UserService.authenticate(db, form_data.username, form_data.password)
    if not user:
        # 记录登录失败日志
        await LoginLogService.record_login(
            db=db,
            username=form_data.username,
            status=0,
            login_ip=client_info["login_ip"],
            failure_reason=2,
            failure_message="用户名或密码错误",
            user_agent=client_info["user_agent"],
            browser_type=client_info["browser_type"],
            os_type=client_info["os_type"],
            device_type=client_info["device_type"],
            login_type="password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if not user.is_active:
        await LoginLogService.record_login(
            db=db,
            username=form_data.username,
            user_id=user.id,
            status=0,
            login_ip=client_info["login_ip"],
            failure_reason=3,
            failure_message="用户已被禁用",
            user_agent=client_info["user_agent"],
            browser_type=client_info["browser_type"],
            os_type=client_info["os_type"],
            device_type=client_info["device_type"],
            login_type="password",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    if user.user_status != 1:
        status_msg = {0: "用户已禁用", 2: "用户已锁定"}.get(user.user_status, "用户状态异常")
        failure_reason = 3 if user.user_status == 0 else 4
        await LoginLogService.record_login(
            db=db,
            username=form_data.username,
            user_id=user.id,
            status=0,
            login_ip=client_info["login_ip"],
            failure_reason=failure_reason,
            failure_message=status_msg,
            user_agent=client_info["user_agent"],
            browser_type=client_info["browser_type"],
            os_type=client_info["os_type"],
            device_type=client_info["device_type"],
            login_type="password",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=status_msg
        )
    
    # 生成token（token中只存身份标识，不存角色等动态信息）
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {
        "sub": user.id,
        "username": user.username,
    }
    access_token = create_access_token(token_data, access_token_expires, device_id=device_id)
    refresh_token = create_refresh_token(token_data, refresh_token_expires, device_id=device_id)
    
    # 将用户动态信息缓存到 Redis（中间件从此处获取角色等信息）
    from utils.user_info_cache import set_cached_user_info
    role_ids = await UserService.get_user_role_ids(db, user.id)
    await set_cached_user_info(user.id, role_ids, user.dept_id, user.is_superuser)
    
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
    await redis.set(
        f"{REFRESH_TOKEN_PREFIX}{user.id}:{device_id}",
        refresh_token,
        ex=int(refresh_token_expires.total_seconds())
    )
    
    # 存储 access token（用于判断设备在线状态）
    await redis.set(
        f"access_token:{user.id}:{device_id}",
        access_token,
        ex=int(access_token_expires.total_seconds())
    )
    
    # 存储设备信息
    device_info_key = f"device_info:{user.id}:{device_id}"
    await redis.hset(device_info_key, mapping={
        "device_type": client_info["device_type"],
        "browser_type": client_info["browser_type"] or "Unknown",
        "os_type": client_info["os_type"] or "Unknown",
        "ip_address": client_info["login_ip"],
        "last_active_time": datetime.now(timezone.utc).isoformat()
    })
    await redis.expire(device_info_key, int(refresh_token_expires.total_seconds()))
    
    # 更新最后登录时间
    await UserService.update_login_info(db, user.id, login_type="password")
    
    # 记录登录成功日志
    await LoginLogService.record_login(
        db=db,
        username=user.username,
        user_id=user.id,
        status=1,
        login_ip=client_info["login_ip"],
        user_agent=client_info["user_agent"],
        browser_type=client_info["browser_type"],
        os_type=client_info["os_type"],
        device_type=client_info["device_type"],
        login_type="password",
    )
    
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer",
        expireTime=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh_token", response_model=TokenResponse, summary="刷新Token")
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    使用refresh_token获取新的access_token
    
    - **refresh_token**: 刷新令牌（在请求体中传递）
    
    返回新的access_token和refresh_token
    """
    print(f"[刷新Token] 收到请求")
    
    # 验证refresh token
    payload = verify_refresh_token(data.refresh_token)
    if not payload:
        print(f"[刷新Token] ❌ JWT验证失败")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    device_id = payload.get("device_id")
    print(f"[刷新Token] JWT验证成功: user_id={user_id}, device_id={device_id}")
    
    if not user_id:
        print(f"[刷新Token] ❌ user_id为空")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 如果 token 中没有 device_id，使用当前请求生成（兼容旧版本）
    if not device_id:
        device_id = get_device_id(request)
        print(f"[刷新Token] 生成device_id: {device_id}")
    
    # 检查refresh token是否在Redis中（防止已登出的token被使用）
    redis = await RedisClient.get_client()
    redis_key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{device_id}"
    redis_key_prev = f"{REFRESH_TOKEN_PREFIX}{user_id}:{device_id}:prev"
    
    stored_token = await redis.get(redis_key)
    stored_prev_token = await redis.get(redis_key_prev)
    
    print(f"[刷新Token] Redis检查: current={stored_token is not None}, prev={stored_prev_token is not None}")
    
    # 如果Redis中没有任何token，说明用户已登出
    if not stored_token:
        print(f"[刷新Token] ❌ Redis中没有token，用户可能已登出")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证token：当前token或上一个token都可以（处理并发刷新）
    is_current_token = (stored_token == data.refresh_token)
    is_prev_token = (stored_prev_token == data.refresh_token)
    
    print(f"[刷新Token] Token匹配: current={is_current_token}, prev={is_prev_token}")
    
    if not is_current_token and not is_prev_token:
        print(f"[刷新Token] ❌ Token不匹配")
        print(f"[刷新Token] 请求token前50字符: {data.refresh_token[:50]}")
        print(f"[刷新Token] Redis current前50字符: {stored_token[:50] if stored_token else 'None'}")
        print(f"[刷新Token] Redis prev前50字符: {stored_prev_token[:50] if stored_prev_token else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否存在且有效
    user = await UserService.get_by_id(db, user_id)
    if not user or not user.is_active or user.user_status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成新的token（token中只存身份标识）
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    token_data = {
        "sub": user.id,
        "username": user.username,
    }
    new_access_token = create_access_token(token_data, access_token_expires, device_id=device_id)
    new_refresh_token = create_refresh_token(token_data, refresh_token_expires, device_id=device_id)
    
    # 刷新 Redis 用户信息缓存（确保角色等信息是最新的）
    from utils.user_info_cache import set_cached_user_info
    role_ids = await UserService.get_user_role_ids(db, user.id)
    await set_cached_user_info(user.id, role_ids, user.dept_id, user.is_superuser)
    
    # 更新Redis中的refresh token（使用设备标识）
    redis = await RedisClient.get_client()
    
    # 保存当前token为上一个token（用于处理并发刷新）
    # 只有当使用的是当前token时才保存，避免旧token被重复使用
    if is_current_token and stored_token:
        await redis.set(
            f"{REFRESH_TOKEN_PREFIX}{user.id}:{device_id}:prev",
            stored_token,
            ex=60  # 上一个token只保留60秒，足够处理并发请求
        )
    
    # 存储新的refresh token
    await redis.set(
        f"{REFRESH_TOKEN_PREFIX}{user.id}:{device_id}",
        new_refresh_token,
        ex=int(refresh_token_expires.total_seconds())
    )
    
    # 更新 access token（用于判断设备在线状态）
    await redis.set(
        f"access_token:{user.id}:{device_id}",
        new_access_token,
        ex=int(access_token_expires.total_seconds())
    )
    
    return TokenResponse(
        accessToken=new_access_token,
        refreshToken=new_refresh_token,
        tokenType="bearer",
        expireTime=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/logout", response_model=ResponseModel, summary="用户登出")
async def logout(request: Request):
    """
    用户登出
    
    需要携带有效的access_token
    """
    user_id = request.state.user_id
    device_id = get_device_id(request)
    
    # 删除Redis中的 refresh token 和 access token（仅删除当前设备的token）
    redis = await RedisClient.get_client()
    await redis.delete(f"{REFRESH_TOKEN_PREFIX}{user_id}:{device_id}")
    await redis.delete(f"{REFRESH_TOKEN_PREFIX}{user_id}:{device_id}:prev")
    await redis.delete(f"access_token:{user_id}:{device_id}")
    
    return ResponseModel(message="登出成功")


@router.get("/userinfo", response_model=LoginUserInfo, summary="获取当前用户信息")
async def get_me(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前登录用户信息
    
    需要携带有效的access_token
    """
    # 获取岗位名称
    post_name = None
    if hasattr(current_user, 'post') and current_user.post:
        post_name = current_user.post.name
    
    # 获取角色ID列表
    role_ids = await UserService.get_user_role_ids(db, current_user.id)
    
    return LoginUserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        mobile=current_user.mobile,
        avatar=current_user.avatar,
        name=current_user.name,
        gender=current_user.gender if current_user.gender is not None else 0,
        gender_display=current_user.get_gender_display(),
        user_type=current_user.user_type if current_user.user_type is not None else 1,
        user_type_display=current_user.get_user_type_display(),
        user_status=current_user.user_status if current_user.user_status is not None else 1,
        user_status_display=current_user.get_user_status_display(),
        birthday=current_user.birthday,
        city=current_user.city,
        address=current_user.address,
        bio=current_user.bio,
        is_superuser=current_user.is_superuser,
        is_active=current_user.is_active,
        dept_id=current_user.dept_id,
        post_id=current_user.post_id,
        post_name=post_name,
        manager_id=current_user.manager_id,
        role_ids=role_ids,
        last_login=current_user.last_login,
        last_login_ip=current_user.last_login_ip,
        last_login_type=current_user.last_login_type,
        sort=current_user.sort,
        is_deleted=current_user.is_deleted,
        sys_create_datetime=current_user.sys_create_datetime,
        sys_update_datetime=current_user.sys_update_datetime,
    )


@router.get("/menus", response_model=dict, summary="获取当前用户的菜单")
async def get_user_menus(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户有权访问的菜单树
    
    - 超级管理员返回所有菜单
    - 普通用户返回角色关联的菜单
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from core.menu.model import Menu
    from core.role.model import Role
    
    # 超级管理员获取所有菜单
    if current_user.is_superuser:
        result = await db.execute(
            select(Menu).where(
                Menu.is_deleted == False,  # noqa: E712
                Menu.status == True  # noqa: E712
            ).order_by(Menu.sort, Menu.sys_create_datetime)
        )
        all_menus = list(result.scalars().all())
    else:
        # 普通用户获取角色关联的菜单（支持多角色）
        from core.user.service import UserService
        role_ids = await UserService.get_user_role_ids(db, current_user.id)
        
        if not role_ids:
            return {"menus": [], "home": None}
        
        # 获取所有角色的菜单并合并（去重）
        all_menus_dict = {}
        for role_id in role_ids:
            result = await db.execute(
                select(Role)
                .options(selectinload(Role.menus))
                .where(
                    Role.id == role_id,
                    Role.status == True,  # noqa: E712
                    Role.is_deleted == False  # noqa: E712
                )
            )
            role = result.scalar_one_or_none()
            
            if role and role.menus:
                for menu in role.menus:
                    if menu.status and not menu.is_deleted:
                        all_menus_dict[menu.id] = menu
        
        all_menus = list(all_menus_dict.values())
    
    # 构建菜单树
    menu_map = {}
    root_menus = []
    
    for menu in all_menus:
        menu_node = {
            "id": menu.id,
            "name": menu.name,
            "title": menu.title,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "menu_type": menu.menu_type,
            "parent_id": menu.parent_id,
            "sort": menu.sort,
            "is_hidden": menu.is_hidden,
            "is_cache": menu.is_cache,
            "is_affix": menu.is_affix,
            "redirect": menu.redirect,
            "children": [],
        }
        menu_map[menu.id] = menu_node
    
    # 建立父子关系
    for menu in all_menus:
        if menu.parent_id and menu.parent_id in menu_map:
            menu_map[menu.parent_id]["children"].append(menu_map[menu.id])
        else:
            root_menus.append(menu_map[menu.id])
    
    # 按sort排序
    def sort_menus(menus):
        menus.sort(key=lambda x: x.get("sort", 0))
        for menu in menus:
            if menu.get("children"):
                sort_menus(menu["children"])
    
    sort_menus(root_menus)
    
    # 获取首页
    home = None
    for menu in all_menus:
        if menu.is_affix and menu.menu_type == 1:
            home = menu.path
            break
    
    return {"menus": root_menus, "home": home}


@router.get("/permissions", response_model=dict, summary="获取当前用户的权限")
async def get_user_permissions(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的权限码列表
    
    - 超级管理员返回 ["*"]（代表所有权限）
    - 普通用户返回角色关联的权限码列表
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from core.role.model import Role
    
    # 超级管理员拥有所有权限
    if current_user.is_superuser:
        return {"permissions": ["*"], "is_superuser": True}
    
    # 普通用户获取所有角色关联的权限（支持多角色）
    from core.user.service import UserService
    role_ids = await UserService.get_user_role_ids(db, current_user.id)
    
    if not role_ids:
        return {"permissions": [], "is_superuser": False}
    
    # 遍历所有角色，收集权限码并去重
    permission_codes_set = set()
    for role_id in role_ids:
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(
                Role.id == role_id,
                Role.status == True,  # noqa: E712
                Role.is_deleted == False  # noqa: E712
            )
        )
        role = result.scalar_one_or_none()
        if role and role.permissions:
            for perm in role.permissions:
                if perm.is_active:
                    permission_codes_set.add(perm.code)
    
    return {"permissions": list(permission_codes_set), "is_superuser": False}
