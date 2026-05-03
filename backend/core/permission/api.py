#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Permission API - 权限管理接口
提供权限的 CRUD 操作
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.permission.schema import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PermissionSimple,
    PermissionBatchDeleteIn, PermissionBatchDeleteOut,
    PermissionBatchUpdateStatusIn, PermissionBatchUpdateStatusOut,
    PermissionSearchRequest, PermissionBatchCreateFromRoutesIn, PermissionBatchCreateFromRoutesOut
)
from core.permission.service import PermissionService

router = APIRouter(prefix="/permission", tags=["权限管理"])


@router.post("", response_model=PermissionResponse, summary="创建权限")
async def create_permission(data: PermissionCreate, db: AsyncSession = Depends(get_db)):
    """创建权限"""
    # 检查同一菜单下权限编码唯一性
    if not await PermissionService.check_code_unique(db, data.menu_id, data.code):
        raise HTTPException(status_code=400, detail=f"该菜单下已存在权限编码: {data.code}")
    
    permission = await PermissionService.create(db=db, data=data)
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return await _build_permission_response(db, permission)


@router.get("/all", response_model=List[PermissionResponse], summary="获取所有权限")
async def get_all_permissions(db: AsyncSession = Depends(get_db)):
    """获取所有启用的权限"""
    permissions = await PermissionService.get_all_active(db)
    return [await _build_permission_response(db, p) for p in permissions]


@router.get("", response_model=PaginatedResponse[PermissionResponse], summary="获取权限列表")
async def get_permission_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    name: Optional[str] = Query(None, description="权限名称"),
    code: Optional[str] = Query(None, description="权限编码"),
    menu_id: Optional[str] = Query(None, alias="menu_id", description="菜单ID"),
    permission_type: Optional[int] = Query(None, alias="permission_type", description="权限类型"),
    is_active: Optional[bool] = Query(None, alias="is_active", description="是否启用"),
    db: AsyncSession = Depends(get_db)
):
    """获取权限列表（分页）"""
    from core.permission.model import Permission
    
    filters = []
    if name:
        filters.append(Permission.name.ilike(f"%{name}%"))
    if code:
        filters.append(Permission.code.ilike(f"%{code}%"))
    if menu_id:
        filters.append(Permission.menu_id == menu_id)
    if permission_type is not None:
        filters.append(Permission.permission_type == permission_type)
    if is_active is not None:
        filters.append(Permission.is_active == is_active)
    
    items, total = await PermissionService.get_list(db, page=page, page_size=page_size, filters=filters)
    response_items = [await _build_permission_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.get("/check/unique", response_model=ResponseModel, summary="检查权限唯一性")
async def check_permission_unique(
    menu_id: str = Query(..., alias="menu_id", description="菜单ID"),
    code: str = Query(..., description="权限编码"),
    exclude_id: Optional[str] = Query(None, alias="excludeId", description="排除ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查同一菜单下权限编码唯一性"""
    is_unique = await PermissionService.check_code_unique(db, menu_id, code, exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.post("/batch/delete", response_model=PermissionBatchDeleteOut, summary="批量删除权限")
async def batch_delete_permissions(
    data: PermissionBatchDeleteIn,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """批量删除权限"""
    count = await PermissionService.batch_delete(db, data.ids, hard=hard)
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return PermissionBatchDeleteOut(count=count)


@router.post("/batch/status", response_model=PermissionBatchUpdateStatusOut, summary="批量更新权限状态")
async def batch_update_permission_status(
    data: PermissionBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量更新权限状态"""
    count = await PermissionService.batch_update_status(db, data.ids, data.is_active)
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return PermissionBatchUpdateStatusOut(count=count)


@router.post("/search", response_model=PaginatedResponse[PermissionResponse], summary="搜索权限")
async def search_permission(
    data: PermissionSearchRequest,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """搜索权限"""
    items, total = await PermissionService.search(db, data.keyword, page, page_size)
    response_items = [await _build_permission_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.get("/by/menu/{menu_id}", response_model=List[PermissionResponse], summary="根据菜单ID获取权限")
async def get_permissions_by_menu(
    menu_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据菜单ID获取该菜单下的所有权限"""
    permissions = await PermissionService.get_by_menu(db, menu_id)
    return [await _build_permission_response(db, p) for p in permissions]


@router.get("/by/type/{permission_type}", response_model=List[PermissionResponse], summary="根据类型获取权限")
async def get_permissions_by_type(
    permission_type: int,
    db: AsyncSession = Depends(get_db)
):
    """根据权限类型获取权限列表"""
    if permission_type not in [0, 1, 2, 3]:
        raise HTTPException(status_code=400, detail="权限类型必须在 0-3 之间")
    
    permissions = await PermissionService.get_by_type(db, permission_type)
    return [await _build_permission_response(db, p) for p in permissions]


@router.get("/{permission_id}", response_model=PermissionResponse, summary="获取权限详情")
async def get_permission_by_id(permission_id: str, db: AsyncSession = Depends(get_db)):
    """获取权限详情"""
    permission = await PermissionService.get_by_id(db, permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="权限不存在")
    return await _build_permission_response(db, permission)


@router.put("/{permission_id}", response_model=PermissionResponse, summary="更新权限")
async def update_permission(permission_id: str, data: PermissionUpdate, db: AsyncSession = Depends(get_db)):
    """更新权限"""
    permission = await PermissionService.get_by_id(db, permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    # 检查权限编码唯一性
    menu_id = data.menu_id if data.menu_id else permission.menu_id
    if data.code:
        if not await PermissionService.check_code_unique(db, menu_id, data.code, permission_id):
            raise HTTPException(status_code=400, detail=f"该菜单下已存在权限编码: {data.code}")
    
    permission = await PermissionService.update(db, record_id=permission_id, data=data)
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return await _build_permission_response(db, permission)


@router.patch("/{permission_id}", response_model=PermissionResponse, summary="部分更新权限")
async def patch_permission(permission_id: str, data: PermissionUpdate, db: AsyncSession = Depends(get_db)):
    """部分更新权限（只更新提供的字段）"""
    permission = await PermissionService.get_by_id(db, permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    # 检查权限编码唯一性
    menu_id = data.menu_id if data.menu_id else permission.menu_id
    if data.code:
        if not await PermissionService.check_code_unique(db, menu_id, data.code, permission_id):
            raise HTTPException(status_code=400, detail=f"该菜单下已存在权限编码: {data.code}")
    
    permission = await PermissionService.update(db, record_id=permission_id, data=data)
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return await _build_permission_response(db, permission)


@router.delete("/{permission_id}", response_model=ResponseModel, summary="删除权限")
async def delete_permission(
    permission_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除权限"""
    success = await PermissionService.delete(db, record_id=permission_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="权限不存在")
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return ResponseModel(message="删除成功")


@router.get("/all/routes", response_model=List[dict], summary="获取所有可用的API路由")
async def get_all_routes():
    """
    获取所有已注册的API路由
    用于前端在创建权限时选择
    """
    from main import app
    routes = PermissionService.get_all_routes_from_app(app)
    return routes


@router.post("/batch/create-from-routes", response_model=PermissionBatchCreateFromRoutesOut, summary="从路由批量创建权限")
async def batch_create_permissions_from_routes(
    data: PermissionBatchCreateFromRoutesIn,
    db: AsyncSession = Depends(get_db)
):
    """
    从前端选择的路由批量创建权限
    
    前端会传递：
    - menu_id: 菜单ID
    - routes: 选中的路由列表（已编辑过的权限信息）
    """
    from sqlalchemy import select
    from core.menu.model import Menu
    
    # 验证菜单是否存在
    result = await db.execute(
        select(Menu).where(Menu.id == data.menu_id)
    )
    menu = result.scalar_one_or_none()
    if not menu:
        return PermissionBatchCreateFromRoutesOut(
            created=0,
            skipped=0,
            failed=len(data.routes),
            errors=[f"菜单 {data.menu_id} 不存在"]
        )
    
    # 转换routes为dict列表
    routes_dict = [route.model_dump() for route in data.routes]
    
    created, skipped, failed, errors = await PermissionService.batch_create_from_routes(
        db, data.menu_id, routes_dict
    )
    
    return PermissionBatchCreateFromRoutesOut(
        created=created,
        skipped=skipped,
        failed=failed,
        errors=errors
    )


@router.post("/auto/scan", response_model=dict, summary="自动扫描并生成权限")
async def auto_scan_and_generate_permissions(
    dry_run: bool = Query(default=False, description="如果为true，只预览不实际创建"),
    db: AsyncSession = Depends(get_db)
):
    """
    从FastAPI Router自动扫描所有API端点并生成权限
    
    参数：
    - dry_run: 如果为true，只预览将要生成的权限，不实际创建
    """
    from main import app
    
    result = await PermissionService.auto_generate_permissions(db, app, dry_run=dry_run)
    return result


async def _build_permission_response(db: AsyncSession, permission) -> PermissionResponse:
    """构建权限响应"""
    # 获取菜单名称
    menu_name = None
    if permission.menu_id:
        from core.menu.service import MenuService
        menu = await MenuService.get_by_id(db, permission.menu_id)
        menu_name = menu.name if menu else None
    
    return PermissionResponse(
        id=permission.id,
        menu_id=permission.menu_id,
        menu_name=menu_name,
        name=permission.name,
        code=permission.code,
        permission_type=permission.permission_type,
        permission_type_display=permission.get_permission_type_display(),
        api_path=permission.api_path,
        http_method=permission.http_method,
        http_method_display=permission.get_http_method_display(),
        description=permission.description,
        is_active=permission.is_active,
        sort=permission.sort,
        is_deleted=permission.is_deleted,
        sys_create_datetime=permission.sys_create_datetime,
        sys_update_datetime=permission.sys_update_datetime,
    )
