#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.application.schema import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
)
from core.application.service import ApplicationService

router = APIRouter(prefix="/applications", tags=["应用管理"])


@router.post("/", response_model=ApplicationResponse, summary="创建应用")
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新应用
    - **name**: 应用名称
    - **code**: 应用编码（唯一标识，用于URL路由，只能包含字母、数字、下划线和短横线）
    - **description**: 应用描述（可选）
    - **icon**: 应用图标（可选）
    - **app_type**: 应用类型（可选，默认mixed）
    """
    # 检查编码唯一性
    if not await ApplicationService.check_unique(db, field="code", value=data.code):
        raise HTTPException(status_code=400, detail="应用编码已存在")
    
    # 检查名称唯一性
    if not await ApplicationService.check_unique(db, field="name", value=data.name):
        raise HTTPException(status_code=400, detail="应用名称已存在")
    
    return await ApplicationService.create(db=db, data=data)


@router.get("/", response_model=PaginatedResponse[ApplicationListResponse], summary="获取应用列表")
async def get_applications(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    keyword: str = Query(default=None, description="搜索关键词"),
    app_type: str = Query(default=None, alias="appType", description="应用类型"),
    status: str = Query(default=None, description="状态"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用列表（分页）
    支持按关键词、类型、状态筛选
    """
    items, total = await ApplicationService.search(
        db,
        keyword=keyword,
        app_type=app_type,
        status=status,
        page=page,
        page_size=page_size
    )
    return PaginatedResponse(items=items, total=total)


@router.get("/stats", response_model=ResponseModel, summary="获取应用统计")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    获取应用统计信息
    """
    stats = await ApplicationService.get_stats(db)
    return ResponseModel(message="获取成功", data=stats)


@router.get("/check/unique", response_model=ResponseModel, summary="检查字段唯一性")
async def check_unique(
    field: str = Query(..., description="字段名：code 或 name"),
    value: str = Query(..., description="字段值"),
    exclude_id: str = Query(default=None, alias="excludeId", description="排除的记录ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    检查字段值是否唯一
    """
    allowed_fields = ["code", "name"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")
    
    is_unique = await ApplicationService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(
        message="可用" if is_unique else "已存在",
        data={"unique": is_unique}
    )


@router.get("/code/{code}", response_model=ApplicationResponse, summary="根据编码获取应用")
async def get_application_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据应用编码获取应用详情
    """
    db_obj = await ApplicationService.get_by_code(db, code=code)
    if db_obj is None:
        raise HTTPException(status_code=404, detail="应用不存在")
    return db_obj


@router.get("/{record_id}", response_model=ApplicationResponse, summary="获取应用详情")
async def get_application(
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据ID获取应用详情
    """
    db_obj = await ApplicationService.get_by_id(db, record_id=record_id)
    if db_obj is None:
        raise HTTPException(status_code=404, detail="应用不存在")
    return db_obj


@router.put("/{record_id}", response_model=ApplicationResponse, summary="更新应用")
async def update_application(
    record_id: str,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新应用信息
    """
    # 检查编码唯一性（排除自身）
    if data.code and not await ApplicationService.check_unique(db, field="code", value=data.code, exclude_id=record_id):
        raise HTTPException(status_code=400, detail="应用编码已存在")
    
    # 检查名称唯一性（排除自身）
    if data.name and not await ApplicationService.check_unique(db, field="name", value=data.name, exclude_id=record_id):
        raise HTTPException(status_code=400, detail="应用名称已存在")
    
    db_obj = await ApplicationService.update(db, record_id=record_id, data=data)
    if db_obj is None:
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 清除该应用相关的菜单缓存
    from core.menu.service import MenuService
    await MenuService.invalidate_app_menu_cache(db_obj.code)
    
    return db_obj


@router.post("/{record_id}/publish", response_model=ApplicationResponse, summary="发布应用")
async def publish_application(
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    发布应用；已停用状态也可调用本接口重新启用（状态变为已发布）
    """
    db_obj = await ApplicationService.publish(db, record_id=record_id)
    if db_obj is None:
        raise HTTPException(status_code=404, detail="应用不存在")
    return db_obj


@router.post("/{record_id}/disable", response_model=ApplicationResponse, summary="停用应用")
async def disable_application(
    record_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    停用应用
    """
    db_obj = await ApplicationService.disable(db, record_id=record_id)
    if db_obj is None:
        raise HTTPException(status_code=404, detail="应用不存在")
    return db_obj


@router.delete("/{record_id}", response_model=ResponseModel, summary="删除应用")
async def delete_application(
    record_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除应用
    - **hard=false**: 逻辑删除（默认）
    - **hard=true**: 物理删除
    """
    success = await ApplicationService.delete(db, record_id=record_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="应用不存在")
    return ResponseModel(message="删除成功")
