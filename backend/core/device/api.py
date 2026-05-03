#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设备管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from utils.redis import RedisClient
from utils.client_info import get_device_id, get_client_info
from utils.security import get_current_user
from app.base_schema import ResponseModel
from core.device.schema import DeviceInfo, DeviceListResponse, DeviceRenameRequest
from datetime import datetime, timezone

router = APIRouter(prefix="/devices", tags=["设备管理"])

# Redis中存储refresh token的key前缀
REFRESH_TOKEN_PREFIX = "refresh_token:"
# Redis中存储设备信息的key前缀
DEVICE_INFO_PREFIX = "device_info:"


@router.get("", response_model=DeviceListResponse, summary="获取设备列表")
async def get_devices(
    request: Request,
    current_user=Depends(get_current_user)
):
    """
    获取当前用户的所有登录设备
    
    返回：
    - current_device: 当前设备信息
    - online_devices: 其他在线设备列表
    - total_count: 设备总数
    """
    user_id = current_user.id
    current_device_id = get_device_id(request)
    
    redis = await RedisClient.get_client()
    
    # 查找该用户的所有refresh token
    pattern = f"{REFRESH_TOKEN_PREFIX}{user_id}:*"
    cursor = 0
    devices = []
    
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        
        for key in keys:
            # 提取device_id
            device_id = key.split(":")[-1]
            
            # 检查refresh token是否存在
            token_exists = await redis.exists(key)
            if not token_exists:
                continue
            
            # 获取设备信息
            device_info_key = f"{DEVICE_INFO_PREFIX}{user_id}:{device_id}"
            device_data = await redis.hgetall(device_info_key)
            
            # 检查 access token 是否存在（判断在线状态）
            access_token_key = f"access_token:{user_id}:{device_id}"
            is_online = await redis.exists(access_token_key)
            
            # 构建设备信息
            device = DeviceInfo(
                device_id=device_id,
                device_name=device_data.get("device_name"),
                device_type=device_data.get("device_type"),
                browser_type=device_data.get("browser_type"),
                os_type=device_data.get("os_type"),
                ip_address=device_data.get("ip_address"),
                last_active_time=datetime.fromisoformat(device_data["last_active_time"]) if device_data.get("last_active_time") else None,
                is_current=(device_id == current_device_id),
                is_online=bool(is_online)
            )
            devices.append(device)
        
        if cursor == 0:
            break
    
    # 分离当前设备和其他设备
    current_device = None
    online_devices = []
    
    for device in devices:
        if device.is_current:
            current_device = device
        else:
            online_devices.append(device)
    
    # 按最后活跃时间排序
    online_devices.sort(key=lambda x: x.last_active_time or datetime.min, reverse=True)
    
    return DeviceListResponse(
        current_device=current_device,
        online_devices=online_devices,
        total_count=len(devices)
    )


@router.delete("/{device_id}", response_model=ResponseModel, summary="强制登出指定设备")
async def logout_device(
    device_id: str,
    request: Request,
    current_user=Depends(get_current_user)
):
    """
    强制登出指定设备
    
    删除该设备的refresh token，使其下次刷新时失效
    """
    user_id = current_user.id
    current_device_id = get_device_id(request)
    
    # 不能登出当前设备
    if device_id == current_device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能登出当前设备，请使用登出功能"
        )
    
    redis = await RedisClient.get_client()
    
    # 删除指定设备的 refresh token 和 access token
    token_key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{device_id}"
    access_token_key = f"access_token:{user_id}:{device_id}"
    deleted = await redis.delete(token_key)
    await redis.delete(access_token_key)
    
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在或已登出"
        )
    
    # 删除设备信息
    device_info_key = f"{DEVICE_INFO_PREFIX}{user_id}:{device_id}"
    await redis.delete(device_info_key)
    
    return ResponseModel(message="设备已强制登出")


@router.delete("/logout-others", response_model=ResponseModel, summary="登出其他所有设备")
async def logout_other_devices(
    request: Request,
    current_user=Depends(get_current_user)
):
    """
    登出除当前设备外的所有其他设备
    """
    user_id = current_user.id
    current_device_id = get_device_id(request)
    
    redis = await RedisClient.get_client()
    
    # 查找该用户的所有refresh token
    pattern = f"{REFRESH_TOKEN_PREFIX}{user_id}:*"
    cursor = 0
    deleted_count = 0
    
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        
        for key in keys:
            # 提取device_id
            device_id = key.split(":")[-1]
            
            # 跳过当前设备
            if device_id == current_device_id:
                continue
            
            # 删除其他设备的 refresh token 和 access token
            await redis.delete(key)
            access_token_key = f"access_token:{user_id}:{device_id}"
            await redis.delete(access_token_key)
            
            # 删除设备信息
            device_info_key = f"{DEVICE_INFO_PREFIX}{user_id}:{device_id}"
            await redis.delete(device_info_key)
            
            deleted_count += 1
        
        if cursor == 0:
            break
    
    return ResponseModel(message=f"已登出 {deleted_count} 台其他设备")


@router.post("/{device_id}/rename", response_model=ResponseModel, summary="重命名设备")
async def rename_device(
    device_id: str,
    data: DeviceRenameRequest,
    current_user=Depends(get_current_user)
):
    """
    为设备设置自定义名称
    """
    user_id = current_user.id
    
    redis = await RedisClient.get_client()
    
    # 检查设备是否存在
    token_key = f"{REFRESH_TOKEN_PREFIX}{user_id}:{device_id}"
    exists = await redis.exists(token_key)
    
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    
    # 更新设备名称
    device_info_key = f"{DEVICE_INFO_PREFIX}{user_id}:{device_id}"
    await redis.hset(device_info_key, "device_name", data.device_name)
    
    return ResponseModel(message="设备名称已更新")


@router.get("/statistics", response_model=ResponseModel, summary="获取设备统计信息")
async def get_device_statistics(
    current_user=Depends(get_current_user)
):
    """
    获取设备统计信息
    """
    user_id = current_user.id
    
    redis = await RedisClient.get_client()
    
    # 统计在线设备数量
    pattern = f"{REFRESH_TOKEN_PREFIX}{user_id}:*"
    cursor = 0
    online_count = 0
    
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        online_count += len(keys)
        
        if cursor == 0:
            break
    
    return ResponseModel(
        message="获取成功",
        data={
            "online_count": online_count,
            "total_count": online_count  # 暂时只统计在线设备
        }
    )
