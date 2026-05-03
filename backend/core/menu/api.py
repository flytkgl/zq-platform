#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Menu API - 菜单管理接口
提供菜单的 CRUD 操作和路由树生成
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import PaginatedResponse, ResponseModel
from core.menu.model import Menu
from core.menu.schema import (
    MenuCreate,
    MenuUpdate,
    MenuResponse,
    MenuTreeNode,
    MenuSimple,
    MenuBatchDeleteRequest,
    MenuBatchDeleteResponse,
    MenuPathResponse,
    MenuStatsResponse,
    MenuMoveRequest,
    MenuCheckNameRequest,
    MenuCheckPathRequest,
)
from core.menu.service import MenuService
from utils.security import get_current_user, get_current_user_id

router = APIRouter(prefix="/menu", tags=["菜单管理"])


def _build_menu_response(menu: Menu, level: int = 0, child_count: int = 0) -> MenuResponse:
    """构建菜单响应"""
    return MenuResponse(
        id=menu.id,
        parent_id=menu.parent_id,
        application_id=menu.application_id,
        is_system=menu.is_system,
        name=menu.name,
        title=menu.title,
        authCode=menu.authCode,
        path=menu.path,
        type=menu.type,
        component=menu.component,
        redirect=menu.redirect,
        activePath=menu.activePath,
        query=menu.query,
        noBasicLayout=menu.noBasicLayout,
        icon=menu.icon,
        activeIcon=menu.activeIcon,
        order=menu.order,
        hideInMenu=menu.hideInMenu,
        hideChildrenInMenu=menu.hideChildrenInMenu,
        hideInBreadcrumb=menu.hideInBreadcrumb,
        hideInTab=menu.hideInTab,
        affixTab=menu.affixTab,
        affixTabOrder=menu.affixTabOrder,
        keepAlive=menu.keepAlive,
        maxNumOfOpenTab=menu.maxNumOfOpenTab,
        fullPathKey=menu.fullPathKey if hasattr(menu, 'fullPathKey') else True,
        link=menu.link,
        iframeSrc=menu.iframeSrc,
        openInNewWindow=menu.openInNewWindow,
        badge=menu.badge,
        badgeType=menu.badgeType,
        badgeVariants=menu.badgeVariants,
        sort=menu.sort,
        is_deleted=menu.is_deleted,
        sys_create_datetime=menu.sys_create_datetime,
        sys_update_datetime=menu.sys_update_datetime,
        level=level,
        childCount=child_count,
    )


@router.post("", response_model=MenuResponse, summary="创建菜单")
async def create_menu(
    data: MenuCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建新菜单
    
    - 检查菜单名称唯一性
    - 检查路由路径唯一性
    - 检查父菜单存在性
    """
    # 检查菜单名称是否已存在
    if await MenuService.check_name_exists(db, data.name):
        raise HTTPException(status_code=400, detail=f"菜单名称已存在: {data.name}")
    
    # 检查路由路径是否已存在
    if await MenuService.check_path_exists(db, data.path):
        raise HTTPException(status_code=400, detail=f"路由路径已存在: {data.path}")
    
    # 检查父菜单是否存在
    if data.parent_id:
        parent = await MenuService.get_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="父菜单不存在")
    
    menu = await MenuService.create(db, data)
    await MenuService.invalidate_cache()
    
    level = await MenuService.get_level(db, menu)
    child_count = await MenuService.get_child_count(db, menu.id)
    return _build_menu_response(menu, level, child_count)


@router.get("/get/tree", response_model=List[dict], summary="获取菜单树")
async def get_menu_tree(
    application_id: str = Query(default=None, alias="applicationId", description="应用ID，用于过滤应用菜单"),
    include_system: bool = Query(default=True, alias="includeSystem", description="是否包含系统菜单"),
    db: AsyncSession = Depends(get_db)
):
    """获取菜单树形结构（带缓存）"""
    return await MenuService.get_menu_tree_cached(db, application_id=application_id, include_system=include_system)


@router.get("/route/tree", response_model=List[dict], summary="获取用户路由树")
async def get_route_tree(
    application_code: str = Query(default=None, description="应用编码，用于过滤应用专属菜单"),
    dev_mode: bool = Query(default=False, alias="devMode", description="开发模式：true只返回系统菜单，false只返回应用菜单"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的路由树
    
    - 超级管理员获取所有菜单
    - 普通用户获取其角色关联的菜单
    - 如果提供 application_code：
      - dev_mode=true（开发模式）：只返回系统菜单（is_system=true）
      - dev_mode=false（正常模式）：只返回该应用的专属菜单（application_id=app.id）
    """
    # 获取用户所有角色关联的菜单ID列表（多对多）
    role_menu_ids = None
    if not current_user.is_superuser:
        from core.user.service import UserService
        from core.role.service import RoleService
        
        # 获取用户的所有角色ID
        role_ids = await UserService.get_user_role_ids(db, current_user.id)
        
        if role_ids:
            # 遍历所有角色，收集菜单ID并去重
            menu_id_set = set()
            for role_id in role_ids:
                role = await RoleService.get_by_id_with_relations(db, role_id)
                if role and role.menus:
                    for menu in role.menus:
                        menu_id_set.add(menu.id)
            if menu_id_set:
                role_menu_ids = list(menu_id_set)
    
    return await MenuService.get_user_route_tree(
        db,
        user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        role_menu_ids=role_menu_ids,
        application_code=application_code,
        dev_mode=dev_mode
    )


@router.get("/list", response_model=PaginatedResponse[MenuResponse], summary="获取菜单列表")
async def get_menu_list(
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=100, description="每页数量"),
    name: str = Query(default=None, description="菜单名称"),
    title: str = Query(default=None, description="菜单标题"),
    type: str = Query(default=None, description="菜单类型"),
    parent_id: str = Query(default=None, description="父菜单ID"),
    application_id: str = Query(default=None, alias="applicationId", description="应用ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取菜单列表（分页）"""
    # 构建过滤条件
    filters = {}
    if name:
        filters["name"] = name
    if title:
        filters["title"] = title
    if type:
        filters["type"] = type
    if parent_id:
        filters["parent_id"] = parent_id
    if application_id:
        filters["application_id"] = application_id
    
    items, total = await MenuService.get_list(db, page=page, page_size=pageSize, filters=filters)
    
    # 构建响应
    result_items = []
    for menu in items:
        level = await MenuService.get_level(db, menu)
        child_count = await MenuService.get_child_count(db, menu.id)
        result_items.append(_build_menu_response(menu, level, child_count))
    
    return PaginatedResponse(items=result_items, total=total)


@router.get("/all", response_model=List[MenuSimple], summary="获取所有菜单")
async def get_all_menus(
    application_id: str = Query(default=None, alias="applicationId", description="应用ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取所有菜单（不分页，简化版，用于选择器）"""
    menus = await MenuService.get_all_menus(db, application_id=application_id)
    result = []
    for menu in menus:
        level = await MenuService.get_level(db, menu)
        result.append(MenuSimple(
            id=menu.id,
            name=menu.name,
            title=menu.title,
            path=menu.path,
            type=menu.type,
            parent_id=menu.parent_id,
            level=level,
        ))
    return result


@router.get("/stats", response_model=MenuStatsResponse, summary="获取菜单统计")
async def get_menu_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取菜单统计信息"""
    stats = await MenuService.get_menu_stats(db)
    return MenuStatsResponse(**stats)


@router.get("/by-parent/{parent_id}", response_model=List[dict], summary="根据父菜单获取子菜单")
async def get_menus_by_parent(
    parent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据父菜单ID获取直接子菜单
    
    - parent_id="null" 获取根菜单
    """
    if parent_id == "null":
        parent_id = None
    
    children = await MenuService.get_children(db, parent_id)
    
    result = []
    for menu in children:
        level = await MenuService.get_level(db, menu)
        child_count = await MenuService.get_child_count(db, menu.id)
        result.append({
            "id": menu.id,
            "parent_id": menu.parent_id,
            "name": menu.name,
            "title": menu.title,
            "path": menu.path,
            "type": menu.type,
            "icon": menu.icon,
            "order": menu.order,
            "level": level,
            "childCount": child_count,
        })
    
    return result


@router.get("/path/{menu_id}", response_model=MenuPathResponse, summary="获取菜单路径")
async def get_menu_path(
    menu_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取菜单的完整路径（从根到当前菜单）"""
    menu = await MenuService.get_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    # 获取所有祖先
    ancestors = await MenuService.get_ancestors(db, menu)
    
    path = []
    for ancestor in reversed(ancestors):
        level = await MenuService.get_level(db, ancestor)
        path.append(MenuSimple(
            id=ancestor.id,
            name=ancestor.name,
            title=ancestor.title,
            path=ancestor.path,
            type=ancestor.type,
            parent_id=ancestor.parent_id,
            level=level,
        ))
    
    # 添加当前菜单
    level = await MenuService.get_level(db, menu)
    path.append(MenuSimple(
        id=menu.id,
        name=menu.name,
        title=menu.title,
        path=menu.path,
        type=menu.type,
        parent_id=menu.parent_id,
        level=level,
    ))
    
    return MenuPathResponse(
        menuId=menu.id,
        menuName=menu.title or menu.name,
        path=path,
    )


@router.post("/check/name", response_model=ResponseModel, summary="检查菜单名称")
async def check_menu_name(
    data: MenuCheckNameRequest,
    application_id: str = Query(default=None, alias="applicationId", description="应用ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查菜单名称是否已存在"""
    exists = await MenuService.check_name_exists(db, data.name, data.exclude_id, application_id=application_id)
    return ResponseModel(
        message=f"菜单名称 '{data.name}' 已存在" if exists else "菜单名称可用",
        data={"exists": exists}
    )


@router.post("/check/path", response_model=ResponseModel, summary="检查路由路径")
async def check_menu_path(
    data: MenuCheckPathRequest,
    application_id: str = Query(default=None, alias="applicationId", description="应用ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查路由路径是否已存在"""
    exists = await MenuService.check_path_exists(db, data.path, data.exclude_id, application_id=application_id)
    return ResponseModel(
        message=f"路由路径 '{data.path}' 已存在" if exists else "路由路径可用",
        data={"exists": exists}
    )


@router.post("/move", response_model=ResponseModel, summary="移动菜单")
async def move_menu(
    data: MenuMoveRequest,
    db: AsyncSession = Depends(get_db)
):
    """移动菜单到新的父菜单下"""
    success, message = await MenuService.move_menu(db, data.menuId, data.newParentId)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return ResponseModel(message=message)


@router.post("/batch/delete", response_model=MenuBatchDeleteResponse, summary="批量删除菜单")
async def batch_delete_menus(
    data: MenuBatchDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    批量删除菜单
    
    - 跳过有子菜单的菜单
    - 返回删除失败的ID列表
    """
    failed_ids = []
    success_count = 0
    
    for menu_id in data.ids:
        menu = await MenuService.get_by_id(db, menu_id)
        if not menu:
            failed_ids.append(menu_id)
            continue
        
        if not await MenuService.can_delete(db, menu_id):
            failed_ids.append(menu_id)
            continue
        
        if await MenuService.delete(db, menu_id):
            success_count += 1
        else:
            failed_ids.append(menu_id)
    
    await MenuService.invalidate_cache()
    return MenuBatchDeleteResponse(count=success_count, failedIds=failed_ids)


@router.get("/{menu_id}", response_model=MenuResponse, summary="获取菜单详情")
async def get_menu(
    menu_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个菜单的详细信息"""
    menu = await MenuService.get_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    level = await MenuService.get_level(db, menu)
    child_count = await MenuService.get_child_count(db, menu.id)
    return _build_menu_response(menu, level, child_count)


@router.put("/{menu_id}", response_model=MenuResponse, summary="更新菜单")
async def update_menu(
    menu_id: str,
    data: MenuUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新菜单信息
    
    - 检查菜单名称唯一性（排除自身）
    - 检查路由路径唯一性（排除自身）
    - 防止设置自己为父菜单
    - 防止形成循环引用
    """
    menu = await MenuService.get_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    # 检查菜单名称是否已存在（排除自身）
    if data.name and await MenuService.check_name_exists(db, data.name, menu_id):
        raise HTTPException(status_code=400, detail=f"菜单名称已存在: {data.name}")
    
    # 检查路由路径是否已存在（排除自身）
    if data.path and await MenuService.check_path_exists(db, data.path, menu_id):
        raise HTTPException(status_code=400, detail=f"路由路径已存在: {data.path}")
    
    # 检查父菜单
    if data.parent_id:
        if data.parent_id == menu_id:
            raise HTTPException(status_code=400, detail="不能将自己设置为父菜单")
        
        parent = await MenuService.get_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="父菜单不存在")
        
        # 检查是否会形成循环引用
        ancestors = await MenuService.get_ancestors(db, parent)
        ancestor_ids = [a.id for a in ancestors]
        if menu.id in ancestor_ids:
            raise HTTPException(status_code=400, detail="不能将子菜单设置为父菜单，会形成循环引用")
    
    updated_menu = await MenuService.update(db, menu_id, data)
    await MenuService.invalidate_cache()
    
    level = await MenuService.get_level(db, updated_menu)
    child_count = await MenuService.get_child_count(db, updated_menu.id)
    return _build_menu_response(updated_menu, level, child_count)


@router.delete("/{menu_id}", response_model=ResponseModel, summary="删除菜单")
async def delete_menu(
    menu_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除菜单
    
    - 检查是否有子菜单
    """
    menu = await MenuService.get_by_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    
    if not await MenuService.can_delete(db, menu_id):
        raise HTTPException(status_code=400, detail="该菜单下还有子菜单，无法删除")
    
    success = await MenuService.delete(db, menu_id, hard=hard)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    
    await MenuService.invalidate_cache()
    return ResponseModel(message="删除成功")
