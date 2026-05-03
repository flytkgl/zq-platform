#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dept API - 部门管理接口
提供部门的 CRUD 操作和树形结构查询
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.dept.schema import (
    DeptCreate, DeptUpdate, DeptResponse, DeptTreeNode, DeptSimple,
    DeptBatchDeleteIn, DeptBatchDeleteOut, DeptBatchUpdateStatusIn, DeptBatchUpdateStatusOut,
    DeptPathOut, DeptUserSchema, DeptUserIn, DeptStatsResponse, DeptMoveRequest, DeptSearchRequest
)
from core.dept.service import DeptService

router = APIRouter(prefix="/dept", tags=["部门管理"])


@router.post("", response_model=DeptResponse, summary="创建部门")
async def create_dept(data: DeptCreate, db: AsyncSession = Depends(get_db)):
    """创建部门"""
    # 编码唯一性校验
    if data.code:
        if not await DeptService.check_unique(db, field="code", value=data.code):
            raise HTTPException(status_code=400, detail="部门编码已存在")
    
    # 检查父部门是否存在
    if data.parent_id:
        parent = await DeptService.get_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="父部门不存在")
    
    dept = await DeptService.create(db=db, data=data)
    return _build_dept_response(dept)


@router.get("/tree", response_model=List[DeptTreeNode], summary="获取部门树")
async def get_dept_tree(
    parent_id: Optional[str] = Query(None, alias="parentId", description="父部门ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取部门树形结构"""
    return await DeptService.get_tree(db, parent_id)


@router.get("", response_model=PaginatedResponse[DeptResponse], summary="获取部门列表")
async def get_dept_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    name: Optional[str] = Query(None, description="部门名称"),
    code: Optional[str] = Query(None, description="部门编码"),
    status: Optional[bool] = Query(None, description="部门状态"),
    dept_type: Optional[str] = Query(None, alias="deptType", description="部门类型"),
    parent_id: Optional[str] = Query(None, alias="parentId", description="父部门ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取部门列表（分页）"""
    from core.dept.model import Dept
    
    filters = []
    if name:
        filters.append(Dept.name.ilike(f"%{name}%"))
    if code:
        filters.append(Dept.code.ilike(f"%{code}%"))
    if status is not None:
        filters.append(Dept.status == status)
    if dept_type:
        filters.append(Dept.dept_type == dept_type)
    if parent_id:
        filters.append(Dept.parent_id == parent_id)
    
    items, total = await DeptService.get_list(db, page=page, page_size=page_size, filters=filters)
    return PaginatedResponse(
        items=[_build_dept_response(item) for item in items],
        total=total
    )


@router.get("/simple", response_model=List[DeptSimple], summary="获取部门简单列表")
async def get_dept_simple_list(
    status: Optional[bool] = Query(None, description="部门状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取部门简单列表（用于选择器）"""
    from core.dept.model import Dept
    
    filters = []
    if status is not None:
        filters.append(Dept.status == status)
    
    items, _ = await DeptService.get_list(db, page=1, page_size=1000, filters=filters)
    return [DeptSimple.model_validate(item) for item in items]


@router.get("/export/excel", summary="导出部门Excel")
async def export_dept_excel(db: AsyncSession = Depends(get_db)):
    """导出部门到Excel"""
    output = await DeptService.export_to_excel(db)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=depts.xlsx"}
    )


@router.get("/import/template", summary="下载部门导入模板")
async def download_dept_template():
    """下载部门导入模板"""
    output = DeptService.get_import_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dept_template.xlsx"}
    )


@router.post("/import/excel", response_model=ResponseModel, summary="导入部门Excel")
async def import_dept_excel(
    file: UploadFile = File(..., description="Excel文件(.xlsx)"),
    db: AsyncSession = Depends(get_db)
):
    """从Excel导入部门"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持.xlsx格式")
    
    content = await file.read()
    success, fail = await DeptService.import_from_excel(db, content)
    return ResponseModel(message=f"成功{success}条，失败{fail}条", data={"success": success, "fail": fail})


@router.get("/check/unique", response_model=ResponseModel, summary="检查部门唯一性")
async def check_dept_unique(
    field: str = Query(..., description="字段名"),
    value: str = Query(..., description="字段值"),
    exclude_id: Optional[str] = Query(None, alias="excludeId", description="排除ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查部门字段唯一性"""
    allowed_fields = ["code", "name"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")
    
    is_unique = await DeptService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.post("/batch/delete", response_model=DeptBatchDeleteOut, summary="批量删除部门")
async def batch_delete_depts(
    data: DeptBatchDeleteIn,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """批量删除部门"""
    count, failed_ids = await DeptService.batch_delete(db, data.ids, hard=hard)
    return DeptBatchDeleteOut(count=count, failed_ids=failed_ids)


@router.post("/batch/status", response_model=DeptBatchUpdateStatusOut, summary="批量更新部门状态")
async def batch_update_dept_status(
    data: DeptBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量更新部门状态"""
    count = await DeptService.batch_update_status(db, data.ids, data.status)
    return DeptBatchUpdateStatusOut(count=count)


@router.get("/{dept_id}/children", response_model=List[DeptResponse], summary="获取子部门")
async def get_dept_children(
    dept_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取直接子部门列表"""
    children = await DeptService.get_children(db, dept_id)
    return [_build_dept_response(item) for item in children]


@router.get("/{dept_id}/descendants", response_model=List[DeptResponse], summary="获取所有后代部门")
async def get_dept_descendants(
    dept_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取所有后代部门"""
    descendants = await DeptService.get_descendants(db, dept_id)
    return [_build_dept_response(item) for item in descendants]


@router.get("/{dept_id}/ancestors", response_model=List[DeptResponse], summary="获取所有祖先部门")
async def get_dept_ancestors(
    dept_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取所有祖先部门"""
    ancestors = await DeptService.get_ancestors(db, dept_id)
    return [_build_dept_response(item) for item in ancestors]


@router.get("/{dept_id}", response_model=DeptResponse, summary="获取部门详情")
async def get_dept_by_id(dept_id: str, db: AsyncSession = Depends(get_db)):
    """获取部门详情"""
    dept = await DeptService.get_by_id(db, dept_id)
    if dept is None:
        raise HTTPException(status_code=404, detail="部门不存在")
    return _build_dept_response(dept)


@router.put("/{dept_id}", response_model=DeptResponse, summary="更新部门")
async def update_dept(dept_id: str, data: DeptUpdate, db: AsyncSession = Depends(get_db)):
    """更新部门"""
    # 编码唯一性校验
    if data.code:
        if not await DeptService.check_unique(db, field="code", value=data.code, exclude_id=dept_id):
            raise HTTPException(status_code=400, detail="部门编码已存在")
    
    # 检查父部门是否存在
    if data.parent_id:
        if data.parent_id == dept_id:
            raise HTTPException(status_code=400, detail="不能将自己设为父部门")
        parent = await DeptService.get_by_id(db, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="父部门不存在")
    
    dept = await DeptService.update(db, record_id=dept_id, data=data)
    if dept is None:
        raise HTTPException(status_code=404, detail="部门不存在")
    return _build_dept_response(dept)


@router.delete("/{dept_id}", response_model=ResponseModel, summary="删除部门")
async def delete_dept(
    dept_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除部门"""
    can_del, reason = await DeptService.can_delete(db, dept_id)
    if not can_del:
        raise HTTPException(status_code=400, detail=reason)
    
    success = await DeptService.delete(db, record_id=dept_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="部门不存在")
    return ResponseModel(message="删除成功")


@router.get("/by/parent/{parent_id}", response_model=List[dict], summary="根据父部门ID获取子部门")
async def get_dept_by_parent(
    parent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据父部门ID获取直接子部门
    
    - parent_id="null" 获取根部门
    """
    if parent_id == "null":
        parent_id = None
    
    return await DeptService.get_by_parent(db, parent_id)


@router.post("/search", response_model=List[dict], summary="搜索部门")
async def search_dept(
    data: DeptSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索部门（模糊匹配部门名称或编码）
    
    返回匹配部门及其完整的层级路径
    """
    return await DeptService.search(db, data.keyword)


@router.get("/by/ids", response_model=List[dict], summary="根据ID列表获取部门")
async def get_depts_by_ids(
    ids: str = Query(..., description="部门ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db)
):
    """
    根据部门ID列表批量获取部门信息（包含完整的层级路径）
    """
    dept_ids = [id.strip() for id in ids.split(',') if id.strip()]
    return await DeptService.get_by_ids(db, dept_ids)


@router.get("/path/{dept_id}", response_model=DeptPathOut, summary="获取部门路径")
async def get_dept_path(
    dept_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取部门的完整路径（从根到当前部门）"""
    dept = await DeptService.get_by_id(db, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 获取所有祖先
    ancestors = await DeptService.get_ancestors(db, dept_id)
    
    path = []
    for ancestor in reversed(ancestors):
        path.append(DeptSimple(
            id=ancestor.id,
            name=ancestor.name,
            code=ancestor.code,
            parent_id=ancestor.parent_id,
            level=ancestor.level,
            status=ancestor.status,
        ))
    
    # 添加当前部门
    path.append(DeptSimple(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        parent_id=dept.parent_id,
        level=dept.level,
        status=dept.status,
    ))
    
    return DeptPathOut(
        dept_id=dept.id,
        dept_name=dept.name,
        path=path
    )


@router.get("/stats", response_model=DeptStatsResponse, summary="获取部门统计信息")
async def get_dept_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取部门统计信息"""
    stats = await DeptService.get_stats(db)
    return DeptStatsResponse(**stats)


@router.post("/move", response_model=ResponseModel, summary="移动部门")
async def move_dept(
    data: DeptMoveRequest,
    db: AsyncSession = Depends(get_db)
):
    """移动部门到新的父部门下"""
    success, message = await DeptService.move(db, data.dept_id, data.new_parent_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return ResponseModel(message=message)


@router.get("/users/{dept_id}", response_model=List[DeptUserSchema], summary="获取部门用户列表")
async def get_dept_users(
    dept_id: str,
    include_children: bool = Query(False, alias="includeChildren", description="是否包含子部门用户"),
    db: AsyncSession = Depends(get_db)
):
    """获取部门下的用户列表"""
    dept = await DeptService.get_by_id(db, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    users = await DeptService.get_dept_users(db, dept_id, include_children)
    return [DeptUserSchema.model_validate(user) for user in users]


@router.post("/users/{dept_id}", response_model=ResponseModel, summary="为部门添加用户")
async def add_user_to_dept(
    dept_id: str,
    data: DeptUserIn,
    db: AsyncSession = Depends(get_db)
):
    """将用户添加到部门"""
    dept = await DeptService.get_by_id(db, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    if not data.user_ids:
        raise HTTPException(status_code=400, detail="用户ID列表不能为空")
    
    added_count = await DeptService.add_users_to_dept(db, dept_id, data.user_ids)
    return ResponseModel(message=f"成功添加 {added_count} 个用户")


@router.delete("/users/{dept_id}", response_model=ResponseModel, summary="从部门中移除用户")
async def remove_user_from_dept(
    dept_id: str,
    data: DeptUserIn,
    db: AsyncSession = Depends(get_db)
):
    """从部门中移除用户（支持批量删除）"""
    dept = await DeptService.get_by_id(db, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 优先使用 user_ids（批量），如果没有则使用 user_id（单个）
    user_ids_to_remove = data.user_ids if data.user_ids else ([data.user_id] if data.user_id else [])
    
    if not user_ids_to_remove:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    removed_count = await DeptService.remove_users_from_dept(db, dept_id, user_ids_to_remove)
    return ResponseModel(message=f"成功移除 {removed_count} 个用户")


def _build_dept_response(dept) -> DeptResponse:
    """构建部门响应"""
    return DeptResponse(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        dept_type=dept.dept_type,
        dept_type_display=dept.get_dept_type_display(),
        phone=dept.phone,
        email=dept.email,
        status=dept.status,
        description=dept.description,
        parent_id=dept.parent_id,
        lead_id=dept.lead_id,
        lead_name=dept.lead.name if dept.lead else None,
        level=dept.level,
        path=dept.path,
        sort=dept.sort,
        is_deleted=dept.is_deleted,
        sys_create_datetime=dept.sys_create_datetime,
        sys_update_datetime=dept.sys_update_datetime,
    )
