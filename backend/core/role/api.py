#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Role API - 角色管理接口
提供角色的 CRUD 操作和权限管理
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.role.schema import (
    RoleCreate, RoleUpdate, RoleResponse, RoleDetail, RoleSimple,
    RoleBatchDeleteIn, RoleBatchDeleteOut,
    RoleBatchUpdateStatusIn, RoleBatchUpdateStatusOut,
    RoleUserSchema, RoleUserIn, RoleMenuPermissionUpdateIn,
    RoleSearchRequest, RoleCopyRequest
)
from core.role.service import RoleService

router = APIRouter(prefix="/role", tags=["角色管理"])


@router.post("", response_model=RoleResponse, summary="创建角色")
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    """创建角色"""
    # 编码唯一性校验
    if not await RoleService.check_unique(db, field="code", value=data.code):
        raise HTTPException(status_code=400, detail=f"角色编码已存在: {data.code}")
    
    role = await RoleService.create(db=db, data=data)
    return await _build_role_response(db, role)


@router.get("/all", response_model=List[RoleSimple], summary="获取所有角色（简化版）")
async def get_all_roles(db: AsyncSession = Depends(get_db)):
    """获取所有启用的角色（不分页，简化版，用于选择器）"""
    roles = await RoleService.get_all_active(db)
    return [RoleSimple.model_validate(role) for role in roles]


@router.get("", response_model=PaginatedResponse[RoleResponse], summary="获取角色列表")
async def get_role_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    name: Optional[str] = Query(None, description="角色名称"),
    code: Optional[str] = Query(None, description="角色编码"),
    status: Optional[bool] = Query(None, description="角色状态"),
    role_type: Optional[int] = Query(None, alias="role_type", description="角色类型"),
    db: AsyncSession = Depends(get_db)
):
    """获取角色列表（分页）"""
    from core.role.model import Role
    
    filters = []
    if name:
        filters.append(Role.name.ilike(f"%{name}%"))
    if code:
        filters.append(Role.code.ilike(f"%{code}%"))
    if status is not None:
        filters.append(Role.status == status)
    if role_type is not None:
        filters.append(Role.role_type == role_type)
    
    items, total = await RoleService.get_list(db, page=page, page_size=page_size, filters=filters)
    response_items = [await _build_role_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.get("/check/unique", response_model=ResponseModel, summary="检查角色唯一性")
async def check_role_unique(
    field: str = Query(..., description="字段名"),
    value: str = Query(..., description="字段值"),
    exclude_id: Optional[str] = Query(None, alias="excludeId", description="排除ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查角色字段唯一性"""
    allowed_fields = ["code", "name"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")
    
    is_unique = await RoleService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.post("/batch/delete", response_model=RoleBatchDeleteOut, summary="批量删除角色")
async def batch_delete_roles(
    data: RoleBatchDeleteIn,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """批量删除角色"""
    count, failed_ids = await RoleService.batch_delete(db, data.ids, hard=hard)
    return RoleBatchDeleteOut(count=count, failed_ids=failed_ids)


@router.post("/batch/status", response_model=RoleBatchUpdateStatusOut, summary="批量更新角色状态")
async def batch_update_role_status(
    data: RoleBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量更新角色状态"""
    count = await RoleService.batch_update_status(db, data.ids, data.status)
    return RoleBatchUpdateStatusOut(count=count)


@router.post("/search", response_model=PaginatedResponse[RoleResponse], summary="搜索角色")
async def search_role(
    data: RoleSearchRequest,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """搜索角色"""
    items, total = await RoleService.search(db, data.keyword, page, page_size)
    response_items = [await _build_role_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.get("/by/ids", response_model=List[RoleSimple], summary="根据ID列表获取角色")
async def get_roles_by_ids(
    ids: str = Query(..., description="角色ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db)
):
    """根据角色ID列表批量获取角色信息"""
    role_ids = [id.strip() for id in ids.split(',') if id.strip()]
    roles = await RoleService.get_by_ids(db, role_ids)
    return [RoleSimple.model_validate(role) for role in roles]


@router.get("/users/by/role_id", response_model=PaginatedResponse[RoleUserSchema], summary="获取角色用户列表")
async def get_role_users(
    role_id: str = Query(..., alias="role_id", description="角色ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    username: str = Query(default=None, description="用户名/姓名搜索"),
    db: AsyncSession = Depends(get_db)
):
    """获取角色下的用户列表"""
    role = await RoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    items, total = await RoleService.get_role_users(
        db, role_id, page=page, page_size=page_size, username=username
    )
    return PaginatedResponse(
        items=[RoleUserSchema(**item) for item in items],
        total=total,
    )


@router.post("/users/by/role_id", response_model=ResponseModel, summary="为角色添加用户")
async def add_user_to_role(
    data: RoleUserIn,
    db: AsyncSession = Depends(get_db)
):
    """将用户添加到角色"""
    role = await RoleService.get_by_id(db, data.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if not data.user_ids:
        raise HTTPException(status_code=400, detail="用户ID列表不能为空")
    
    added_count = await RoleService.add_users_to_role(db, data.role_id, data.user_ids)
    return ResponseModel(message=f"成功添加 {added_count} 个用户")


@router.delete("/users/by/role_id", response_model=ResponseModel, summary="从角色中移除用户")
async def remove_user_from_role(
    data: RoleUserIn,
    db: AsyncSession = Depends(get_db)
):
    """从角色中移除用户"""
    role = await RoleService.get_by_id(db, data.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    user_ids_to_remove = data.user_ids if data.user_ids else ([data.user_id] if data.user_id else [])
    
    if not user_ids_to_remove:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    removed_count = await RoleService.remove_users_from_role(db, data.role_id, user_ids_to_remove)
    return ResponseModel(message=f"成功移除 {removed_count} 个用户")


@router.put("/{role_id}/menus-permissions", response_model=ResponseModel, summary="更新角色菜单和权限")
async def update_role_menus_permissions(
    role_id: str,
    data: RoleMenuPermissionUpdateIn,
    db: AsyncSession = Depends(get_db)
):
    """同时更新角色关联的菜单和权限"""
    role = await RoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    success = await RoleService.update_menus_permissions(db, role_id, data.menu_ids, data.permission_ids)
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return ResponseModel(message=f"成功更新 {len(data.menu_ids)} 个菜单和 {len(data.permission_ids)} 个权限")


@router.put("/{role_id}/permissions", response_model=ResponseModel, summary="更新角色权限")
async def update_role_permissions(
    role_id: str,
    data: RoleMenuPermissionUpdateIn,
    db: AsyncSession = Depends(get_db)
):
    """更新角色关联的权限"""
    role = await RoleService.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    success = await RoleService.update_permissions(db, role_id, data.permission_ids)
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    
    # 刷新权限缓存
    from utils.permission import clear_permission_cache
    await clear_permission_cache()
    
    return ResponseModel(message=f"成功更新 {len(data.permission_ids)} 个权限")


@router.get("/menu-permission-tree/{role_id}", response_model=dict, summary="获取角色的菜单权限树")
async def get_role_menu_permission_tree(
    role_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取角色的菜单和权限树形结构，用于角色权限配置界面"""
    role = await RoleService.get_by_id_with_relations(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return await RoleService.get_menu_permission_tree(db, role)


@router.get("/{role_id}/menus", response_model=dict, summary="获取角色菜单列表")
async def get_role_menus(
    role_id: str,
    application_id: Optional[str] = Query(None, alias="applicationId", description="应用ID，子应用访问时只显示该应用的菜单"),
    db: AsyncSession = Depends(get_db)
):
    """获取角色的菜单列表（不包含权限）"""
    role = await RoleService.get_by_id_with_relations(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return await RoleService.get_role_menus(db, role, application_id=application_id)


@router.get("/{role_id}/menu/{menu_id}/permissions", response_model=dict, summary="获取菜单的权限列表")
async def get_menu_permissions(
    role_id: str,
    menu_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取指定菜单的权限列表"""
    role = await RoleService.get_by_id_with_relations(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    return await RoleService.get_menu_permissions(db, role, menu_id)


@router.patch("/{role_id}", response_model=RoleResponse, summary="部分更新角色")
async def patch_role(role_id: str, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    """部分更新角色（只更新提供的字段）"""
    role = await RoleService.get_by_id(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 编码唯一性校验
    if data.code:
        if not await RoleService.check_unique(db, field="code", value=data.code, exclude_id=role_id):
            raise HTTPException(status_code=400, detail=f"角色编码已存在: {data.code}")
    
    # 系统角色不能修改角色类型和编码
    if role.is_system_role():
        if data.role_type is not None and data.role_type != 0:
            raise HTTPException(status_code=400, detail="系统角色不能修改角色类型")
        if data.code and data.code != role.code:
            raise HTTPException(status_code=400, detail="系统角色不能修改角色编码")
    
    role = await RoleService.update(db, record_id=role_id, data=data)
    return await _build_role_response(db, role)


@router.post("/copy/{role_id}", response_model=RoleResponse, summary="复制角色")
async def copy_role(
    role_id: str,
    data: RoleCopyRequest,
    db: AsyncSession = Depends(get_db)
):
    """复制现有角色"""
    # 检查新编码是否已存在
    if not await RoleService.check_unique(db, field="code", value=data.new_code):
        raise HTTPException(status_code=400, detail=f"角色编码已存在: {data.new_code}")
    
    new_role = await RoleService.copy_role(db, role_id, data.new_name, data.new_code)
    if not new_role:
        raise HTTPException(status_code=404, detail="源角色不存在")
    
    return await _build_role_response(db, new_role)


@router.get("/{role_id}", response_model=RoleDetail, summary="获取角色详情")
async def get_role_by_id(role_id: str, db: AsyncSession = Depends(get_db)):
    """获取角色详情（包含关联数据）"""
    role = await RoleService.get_by_id_with_relations(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    return await _build_role_detail(db, role)


@router.put("/{role_id}", response_model=RoleResponse, summary="更新角色")
async def update_role(role_id: str, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    """更新角色"""
    role = await RoleService.get_by_id(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 编码唯一性校验
    if data.code:
        if not await RoleService.check_unique(db, field="code", value=data.code, exclude_id=role_id):
            raise HTTPException(status_code=400, detail=f"角色编码已存在: {data.code}")
    
    # 系统角色不能修改角色类型和编码
    if role.is_system_role():
        if data.role_type is not None and data.role_type != 0:
            raise HTTPException(status_code=400, detail="系统角色不能修改角色类型")
        if data.code and data.code != role.code:
            raise HTTPException(status_code=400, detail="系统角色不能修改角色编码")
    
    role = await RoleService.update(db, record_id=role_id, data=data)
    return await _build_role_response(db, role)


@router.delete("/{role_id}", response_model=ResponseModel, summary="删除角色")
async def delete_role(
    role_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除角色"""
    can_del, reason = await RoleService.can_delete(db, role_id)
    if not can_del:
        raise HTTPException(status_code=400, detail=reason)
    
    success = await RoleService.delete(db, record_id=role_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="角色不存在")
    return ResponseModel(message="删除成功")


async def _build_role_response(db: AsyncSession, role) -> RoleResponse:
    """构建角色响应"""
    user_count = await RoleService.get_user_count(db, role.id)
    
    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        role_type=role.role_type,
        role_type_display=role.get_role_type_display(),
        status=role.status,
        priority=role.priority,
        description=role.description,
        remark=role.remark,
        user_count=user_count,
        menu_count=len(role.menus) if hasattr(role, 'menus') and role.menus else 0,
        permission_count=len(role.permissions) if hasattr(role, 'permissions') and role.permissions else 0,
        can_delete=role.can_delete(),
        sort=role.sort,
        is_deleted=role.is_deleted,
        sys_create_datetime=role.sys_create_datetime,
        sys_update_datetime=role.sys_update_datetime,
    )


async def _build_role_detail(db: AsyncSession, role) -> RoleDetail:
    """构建角色详情响应"""
    user_count = await RoleService.get_user_count(db, role.id)
    
    return RoleDetail(
        id=role.id,
        name=role.name,
        code=role.code,
        role_type=role.role_type,
        role_type_display=role.get_role_type_display(),
        status=role.status,
        priority=role.priority,
        description=role.description,
        remark=role.remark,
        user_count=user_count,
        menu_count=len(role.menus) if role.menus else 0,
        permission_count=len(role.permissions) if role.permissions else 0,
        can_delete=role.can_delete(),
        sort=role.sort,
        is_deleted=role.is_deleted,
        sys_create_datetime=role.sys_create_datetime,
        sys_update_datetime=role.sys_update_datetime,
        menu_ids=[m.id for m in role.menus] if role.menus else [],
        permission_ids=[p.id for p in role.permissions] if role.permissions else [],
        dept_ids=[d.id for d in role.depts] if role.depts else [],
    )
