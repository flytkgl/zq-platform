#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI Config API - UI配置管理接口
提供UI配置的 CRUD 操作
"""
import json
from typing import Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.ui_config.model import UIConfig
from core.ui_config.schema import (
    UIConfigCreate, UIConfigUpdate, UIConfigResponse, UIConfigSimple,
    UIConfigValueUpdate, PreferencesConfigResponse
)
from core.ui_config.service import UIConfigService

router = APIRouter(prefix="/ui_config", tags=["UI配置管理"])


@router.get("/preferences", summary="获取前端偏好配置")
async def get_preferences(
    application_id: Optional[str] = Query(default=None, alias="applicationId", description="应用ID，不传则获取主应用配置"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取前端偏好设置配置
    返回格式与前端 Preferences 类型一致
    此接口无需认证，用于前端初始化时加载配置
    
    - 不传 applicationId：获取主应用配置
    - 传 applicationId：获取子应用配置，如果子应用没有配置则回退到主应用配置
    """
    config = await UIConfigService.get_preferences_config(db, application_id)
    return config or {}


@router.put("/preferences", response_model=ResponseModel, summary="更新前端偏好配置")
async def update_preferences(
    data: Dict[str, Any],
    application_id: Optional[str] = Query(default=None, alias="applicationId", description="应用ID，不传则更新主应用配置"),
    db: AsyncSession = Depends(get_db)
):
    """
    更新前端偏好设置配置
    
    - 不传 applicationId：更新主应用配置
    - 传 applicationId：更新子应用配置
    """
    config = await UIConfigService.update_preferences_config(db, data, application_id)
    return ResponseModel(message="更新成功", data={"id": config.id})


@router.post("", response_model=UIConfigResponse, summary="创建UI配置")
async def create_ui_config(data: UIConfigCreate, db: AsyncSession = Depends(get_db)):
    """创建UI配置"""
    # 唯一性校验
    if not await UIConfigService.check_unique(db, field="config_key", value=data.config_key):
        raise HTTPException(status_code=400, detail=f"配置键已存在: {data.config_key}")
    
    config = await UIConfigService.create(db=db, data=data)
    return config


@router.get("/all", response_model=list[UIConfigSimple], summary="获取所有UI配置（简化版）")
async def get_all_ui_configs(db: AsyncSession = Depends(get_db)):
    """获取所有启用的UI配置（用于选择器）"""
    configs = await UIConfigService.get_all_active(db)
    return configs


@router.get("", response_model=PaginatedResponse[UIConfigResponse], summary="获取UI配置列表")
async def get_ui_config_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    config_key: Optional[str] = Query(default=None, alias="configKey", description="配置键"),
    config_type: Optional[str] = Query(default=None, alias="configType", description="配置类型"),
    status: Optional[bool] = Query(default=None, description="状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取UI配置列表（分页）"""
    filters = []
    if config_key:
        filters.append(UIConfig.config_key.ilike(f"%{config_key}%"))
    if config_type:
        filters.append(UIConfig.config_type == config_type)
    if status is not None:
        filters.append(UIConfig.status == status)
    
    items, total = await UIConfigService.get_list(db, page=page, page_size=page_size, filters=filters)
    return PaginatedResponse(items=items, total=total)


@router.get("/by/type/{config_type}", response_model=list[UIConfigResponse], summary="根据类型获取UI配置")
async def get_ui_configs_by_type(config_type: str, db: AsyncSession = Depends(get_db)):
    """根据配置类型获取UI配置列表"""
    configs = await UIConfigService.get_by_type(db, config_type)
    return configs


@router.get("/by/key/{config_key}", response_model=UIConfigResponse, summary="根据配置键获取UI配置")
async def get_ui_config_by_key(config_key: str, db: AsyncSession = Depends(get_db)):
    """根据配置键获取UI配置"""
    config = await UIConfigService.get_by_key(db, config_key)
    if config is None:
        raise HTTPException(status_code=404, detail=f"配置键不存在: {config_key}")
    return config


@router.get("/value/{config_key}", response_model=ResponseModel, summary="获取配置值")
async def get_ui_config_value(config_key: str, db: AsyncSession = Depends(get_db)):
    """获取配置值（解析JSON后返回）"""
    value = await UIConfigService.get_config_value(db, config_key)
    return ResponseModel(data=value)


@router.put("/value/{config_key}", response_model=ResponseModel, summary="更新配置值")
async def update_ui_config_value(
    config_key: str,
    data: UIConfigValueUpdate,
    db: AsyncSession = Depends(get_db)
):
    """根据配置键更新配置值"""
    config = await UIConfigService.update_value_by_key(db, config_key, data.config_value)
    if config is None:
        raise HTTPException(status_code=404, detail=f"配置键不存在: {config_key}")
    return ResponseModel(message="更新成功")


@router.get("/check/unique", response_model=ResponseModel, summary="检查UI配置唯一性")
async def check_ui_config_unique(
    field: str = Query(..., description="字段名"),
    value: str = Query(..., description="字段值"),
    exclude_id: str = Query(default=None, alias="excludeId", description="排除ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查UI配置字段唯一性"""
    allowed_fields = ["config_key"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")
    
    is_unique = await UIConfigService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.get("/{config_id}", response_model=UIConfigResponse, summary="获取UI配置详情")
async def get_ui_config_by_id(config_id: str, db: AsyncSession = Depends(get_db)):
    """获取UI配置详情"""
    config = await UIConfigService.get_by_id(db, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="UI配置不存在")
    return config


@router.put("/{config_id}", response_model=UIConfigResponse, summary="更新UI配置")
async def update_ui_config(config_id: str, data: UIConfigUpdate, db: AsyncSession = Depends(get_db)):
    """更新UI配置"""
    # 唯一性校验（排除自身）
    if data.config_key and not await UIConfigService.check_unique(db, field="config_key", value=data.config_key, exclude_id=config_id):
        raise HTTPException(status_code=400, detail=f"配置键已存在: {data.config_key}")
    
    config = await UIConfigService.update(db, record_id=config_id, data=data)
    if config is None:
        raise HTTPException(status_code=404, detail="UI配置不存在")
    return config


@router.delete("/{config_id}", response_model=ResponseModel, summary="删除UI配置")
async def delete_ui_config(
    config_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除UI配置"""
    success = await UIConfigService.delete(db, record_id=config_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="UI配置不存在")
    return ResponseModel(message="删除成功")
