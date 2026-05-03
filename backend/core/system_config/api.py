#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SystemConfig API - 系统配置管理接口
提供 SSO 登录和消息通知等系统配置的前端管理接口
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import ResponseModel
from app.config_manager import config_manager, GROUP_ENV_MAPPING
from core.system_config.schema import GroupConfigUpdate
from core.system_config.service import SystemConfigService

router = APIRouter(prefix="/system-config", tags=["系统配置管理"])


@router.get("/groups", summary="获取所有配置分组定义")
async def get_groups():
    """获取所有配置分组及其字段定义"""
    return config_manager.get_group_list()


@router.get("/all", summary="获取所有分组配置")
async def get_all_configs():
    """获取所有分组配置（敏感字段脱敏）"""
    return await SystemConfigService.get_all_groups_config(mask_secrets=True)


@router.get("/group/{group}", summary="获取分组配置")
async def get_group_config(group: str):
    """
    获取指定分组的配置（敏感字段脱敏）

    三级获取优先级: Redis → 数据库 → env 配置文件
    """
    if group not in GROUP_ENV_MAPPING:
        raise HTTPException(status_code=400, detail=f"不支持的配置分组: {group}")

    return await SystemConfigService.get_group_config(group, mask_secrets=True)


@router.put("/group/{group}", response_model=ResponseModel, summary="更新分组配置")
async def update_group_config(
    group: str,
    data: GroupConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    批量更新指定分组的配置

    - 敏感字段如果传入脱敏值（含 ***），则跳过不更新
    - 更新后自动清除 Redis 缓存
    """
    if group not in GROUP_ENV_MAPPING:
        raise HTTPException(status_code=400, detail=f"不支持的配置分组: {group}")

    updated = await SystemConfigService.update_group_config(db, group, data.configs)
    return ResponseModel(message="更新成功", data=updated)


@router.delete("/group/{group}", response_model=ResponseModel, summary="删除分组配置")
async def delete_group_config(
    group: str,
    db: AsyncSession = Depends(get_db),
):
    """删除指定分组的数据库配置（恢复为 env 配置文件默认值）"""
    if group not in GROUP_ENV_MAPPING:
        raise HTTPException(status_code=400, detail=f"不支持的配置分组: {group}")

    success = await SystemConfigService.delete_group_config(db, group)
    return ResponseModel(message="已恢复为默认配置" if success else "该分组无自定义配置")


@router.post("/cache/warmup", response_model=ResponseModel, summary="预热配置缓存")
async def warmup_cache():
    """手动预热所有配置到 Redis 缓存"""
    await config_manager.warmup()
    return ResponseModel(message="缓存预热完成")


@router.delete("/cache", response_model=ResponseModel, summary="清除配置缓存")
async def clear_cache():
    """清除所有配置的 Redis 缓存"""
    await config_manager.invalidate_all()
    return ResponseModel(message="缓存已清除")
