#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post API - 岗位管理接口
提供岗位的 CRUD 操作和用户管理
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.post.schema import (
    PostCreate, PostUpdate, PostResponse, PostSimple,
    PostBatchDeleteIn, PostBatchDeleteOut, PostBatchUpdateStatusIn, PostBatchUpdateStatusOut,
    PostUserSchema, PostUserIn, PostStatsResponse, PostSearchRequest
)
from core.post.service import PostService

router = APIRouter(prefix="/post", tags=["岗位管理"])


@router.post("", response_model=PostResponse, summary="创建岗位")
async def create_post(
    data: PostCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建岗位（自动记录创建人）"""
    # 编码唯一性校验
    if not await PostService.check_unique(db, field="code", value=data.code):
        raise HTTPException(status_code=400, detail=f"岗位编码已存在: {data.code}")
    
    post = await PostService.create(db=db, data=data)
    return await _build_post_response(db, post)


@router.get("/all", response_model=List[PostSimple], summary="获取所有岗位（简化版）")
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    """获取所有启用的岗位（不分页，简化版，用于选择器）"""
    posts = await PostService.get_all_simple(db)
    return [PostSimple.model_validate(post) for post in posts]


@router.get("", response_model=PaginatedResponse[PostResponse], summary="获取岗位列表")
async def get_post_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    name: Optional[str] = Query(None, description="岗位名称"),
    code: Optional[str] = Query(None, description="岗位编码"),
    post_type: Optional[int] = Query(None, alias="post_type", description="岗位类型"),
    post_level: Optional[int] = Query(None, alias="post_level", description="岗位级别"),
    status: Optional[bool] = Query(None, description="岗位状态"),
    dept_id: Optional[str] = Query(None, alias="dept_id", description="部门ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取岗位列表（分页）"""
    from core.post.model import Post
    
    filters = []
    if name:
        filters.append(Post.name.ilike(f"%{name}%"))
    if code:
        filters.append(Post.code.ilike(f"%{code}%"))
    if post_type is not None:
        filters.append(Post.post_type == post_type)
    if post_level is not None:
        filters.append(Post.post_level == post_level)
    if status is not None:
        filters.append(Post.status == status)
    if dept_id:
        filters.append(Post.dept_id == dept_id)
    
    items, total = await PostService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        filters=filters
    )
    
    response_items = [await _build_post_response(db, item) for item in items]
    
    return PaginatedResponse(items=response_items, total=total)


@router.get("/export/excel", summary="导出岗位Excel")
async def export_post_excel(
    db: AsyncSession = Depends(get_db)
):
    """导出岗位到Excel"""
    output = await PostService.export_to_excel(
        db=db,
        data_converter=PostService._export_converter
    )
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=posts.xlsx"}
    )


@router.get("/import/template", summary="下载岗位导入模板")
async def download_post_template():
    """下载岗位导入模板"""
    output = PostService.get_import_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=post_template.xlsx"}
    )


@router.post("/import/excel", response_model=ResponseModel, summary="导入岗位Excel")
async def import_post_excel(
    file: UploadFile = File(..., description="Excel文件(.xlsx)"),
    db: AsyncSession = Depends(get_db)
):
    """从Excel导入岗位"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持.xlsx格式")
    
    content = await file.read()
    success, fail = await PostService.import_from_excel(db, content)
    return ResponseModel(message=f"成功{success}条，失败{fail}条", data={"success": success, "fail": fail})


@router.get("/check/unique", response_model=ResponseModel, summary="检查岗位唯一性")
async def check_post_unique(
    field: str = Query(..., description="字段名"),
    value: str = Query(..., description="字段值"),
    exclude_id: Optional[str] = Query(None, alias="excludeId", description="排除ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查岗位字段唯一性"""
    allowed_fields = ["code", "name"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")
    
    is_unique = await PostService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.post("/batch/delete", response_model=PostBatchDeleteOut, summary="批量删除岗位")
async def batch_delete_posts(
    data: PostBatchDeleteIn,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """批量删除岗位"""
    count, failed_ids = await PostService.batch_delete(db, data.ids, hard=hard)
    return PostBatchDeleteOut(count=count, failed_ids=failed_ids)


@router.post("/batch/status", response_model=PostBatchUpdateStatusOut, summary="批量更新岗位状态")
async def batch_update_post_status(
    data: PostBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量更新岗位状态"""
    count = await PostService.batch_update_status(db, data.ids, data.status)
    return PostBatchUpdateStatusOut(count=count)


@router.post("/search", response_model=PaginatedResponse[PostResponse], summary="搜索岗位")
async def search_post(
    data: PostSearchRequest,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """搜索岗位（模糊匹配名称、编码、描述，自动应用数据权限过滤）"""
    items, total = await PostService.search_with_data_scope(
        db=db,
        keyword=data.keyword,
        page=page,
        page_size=page_size
    )
    response_items = [await _build_post_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.get("/stats", response_model=PostStatsResponse, summary="获取岗位统计信息")
async def get_post_stats(db: AsyncSession = Depends(get_db)):
    """获取岗位统计信息"""
    stats = await PostService.get_stats(db)
    return PostStatsResponse(**stats)


@router.get("/by/ids", response_model=List[PostResponse], summary="根据ID列表获取岗位")
async def get_posts_by_ids(
    ids: str = Query(..., description="岗位ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db)
):
    """根据岗位ID列表批量获取岗位信息"""
    post_ids = [id.strip() for id in ids.split(',') if id.strip()]
    posts = await PostService.get_by_ids(db, post_ids)
    return [await _build_post_response(db, post) for post in posts]


@router.get("/by/dept/{dept_id}", response_model=List[PostSimple], summary="根据部门ID获取岗位")
async def get_posts_by_dept(
    dept_id: str,
    db: AsyncSession = Depends(get_db)
):
    """根据部门ID获取该部门的所有岗位"""
    posts = await PostService.get_by_dept(db, dept_id)
    return [PostSimple.model_validate(post) for post in posts]


@router.get("/by/type/{post_type}", response_model=List[PostSimple], summary="根据类型获取岗位")
async def get_posts_by_type(
    post_type: int,
    db: AsyncSession = Depends(get_db)
):
    """根据岗位类型获取岗位列表"""
    if post_type not in [0, 1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="岗位类型必须在 0-4 之间")
    
    posts = await PostService.get_by_type(db, post_type)
    return [PostSimple.model_validate(post) for post in posts]


@router.get("/by/level/{post_level}", response_model=List[PostSimple], summary="根据级别获取岗位")
async def get_posts_by_level(
    post_level: int,
    db: AsyncSession = Depends(get_db)
):
    """根据岗位级别获取岗位列表"""
    if post_level not in [0, 1, 2, 3]:
        raise HTTPException(status_code=400, detail="岗位级别必须在 0-3 之间")
    
    posts = await PostService.get_by_level(db, post_level)
    return [PostSimple.model_validate(post) for post in posts]


@router.get("/users/by/post_id", response_model=PaginatedResponse[PostUserSchema], summary="获取岗位用户列表")
async def get_post_users(
    post_id: str = Query(..., alias="post_id", description="岗位ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取岗位下的用户列表"""
    post = await PostService.get_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    users = await PostService.get_post_users(db, post_id)
    
    # 分页处理
    total = len(users)
    start = (page - 1) * page_size
    end = start + page_size
    paged_users = users[start:end]
    
    result = []
    for user in paged_users:
        dept_name = None
        if user.dept_id:
            from core.dept.service import DeptService
            dept = await DeptService.get_by_id(db, user.dept_id)
            dept_name = dept.name if dept else None
        
        result.append(PostUserSchema(
            id=user.id,
            name=user.name,
            username=user.username,
            avatar=user.avatar,
            email=user.email,
            dept_name=dept_name
        ))
    return PaginatedResponse(items=result, total=total)


@router.post("/users/by/post_id", response_model=ResponseModel, summary="为岗位添加用户")
async def add_user_to_post(
    data: PostUserIn,
    db: AsyncSession = Depends(get_db)
):
    """将用户添加到岗位"""
    post = await PostService.get_by_id(db, data.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    if not data.user_ids:
        raise HTTPException(status_code=400, detail="用户ID列表不能为空")
    
    added_count = await PostService.add_users_to_post(db, data.post_id, data.user_ids)
    return ResponseModel(message=f"成功添加 {added_count} 个用户")


@router.delete("/users/{post_id}", response_model=ResponseModel, summary="从岗位中移除用户")
async def remove_user_from_post(
    post_id: str,
    data: PostUserIn,
    db: AsyncSession = Depends(get_db)
):
    """从岗位中移除用户（支持批量删除）"""
    post = await PostService.get_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    # 优先使用 user_ids（批量），如果没有则使用 user_id（单个）
    user_ids_to_remove = data.user_ids if data.user_ids else ([data.user_id] if data.user_id else [])
    
    if not user_ids_to_remove:
        raise HTTPException(status_code=400, detail="用户ID不能为空")
    
    removed_count = await PostService.remove_users_from_post(db, post_id, user_ids_to_remove)
    return ResponseModel(message=f"成功移除 {removed_count} 个用户")


@router.get("/{post_id}", response_model=PostResponse, summary="获取岗位详情")
async def get_post_by_id(post_id: str, db: AsyncSession = Depends(get_db)):
    """获取岗位详情"""
    post = await PostService.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    
    return await _build_post_response(db, post)


@router.put("/{post_id}", response_model=PostResponse, summary="更新岗位")
async def update_post(
    post_id: str,
    data: PostUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新岗位（自动记录修改人）"""
    # 编码唯一性校验
    if data.code:
        if not await PostService.check_unique(db, field="code", value=data.code, exclude_id=post_id):
            raise HTTPException(status_code=400, detail=f"岗位编码已存在: {data.code}")
    
    # 自动从上下文获取当前用户ID并填充 sys_modifier_id
    post = await PostService.update(db, record_id=post_id, data=data)
    if post is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return await _build_post_response(db, post)


@router.delete("/{post_id}", response_model=ResponseModel, summary="删除岗位")
async def delete_post(
    post_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除岗位"""
    can_del, reason = await PostService.can_delete(db, post_id)
    if not can_del:
        raise HTTPException(status_code=400, detail=reason)
    
    success = await PostService.delete(db, record_id=post_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return ResponseModel(message="删除成功")


async def _build_post_response(db: AsyncSession, post) -> PostResponse:
    """构建岗位响应"""
    # 获取部门名称
    dept_name = None
    if post.dept_id:
        from core.dept.service import DeptService
        dept = await DeptService.get_by_id(db, post.dept_id)
        dept_name = dept.name if dept else None
    
    # 获取用户数量
    user_count = await PostService.get_user_count(db, post.id)
    
    return PostResponse(
        id=post.id,
        name=post.name,
        code=post.code,
        post_type=post.post_type,
        post_type_display=post.get_post_type_display(),
        post_level=post.post_level,
        post_level_display=post.get_post_level_display(),
        status=post.status,
        description=post.description,
        dept_id=post.dept_id,
        dept_name=dept_name,
        user_count=user_count,
        sort=post.sort,
        is_deleted=post.is_deleted,
        sys_create_datetime=post.sys_create_datetime,
        sys_update_datetime=post.sys_update_datetime,
    )
