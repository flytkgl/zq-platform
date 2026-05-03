from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from zq_demo.schema import DemoCreate, DemoUpdate, DemoResponse
from zq_demo.service import DemoService
from zq_demo.model import Demo

router = APIRouter(prefix="/demos", tags=["Demo管理"])


@router.post("", response_model=DemoResponse, summary="创建Demo")
async def create_demo(demo: DemoCreate, db: AsyncSession = Depends(get_db)):
    """
    创建新Demo（自动记录创建人和部门）
    - **title**: 标题
    - **content**: 内容（可选）
    - **status**: 状态（0=草稿，1=发布，2=归档）
    - **priority**: 优先级（0=低，1=中，2=高）
    - **is_active**: 是否激活（默认true）
    """
    # 检查标题唯一性
    if not await DemoService.check_unique(db, field="title", value=demo.title):
        raise HTTPException(status_code=400, detail="标题已存在")
    
    return await DemoService.create(db=db, data=demo)


@router.get("", response_model=PaginatedResponse[DemoResponse], summary="获取Demo列表")
async def get_demos(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    title: Optional[str] = Query(None, description="标题（模糊搜索）"),
    status: Optional[int] = Query(None, description="状态筛选"),
    priority: Optional[int] = Query(None, description="优先级筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取Demo列表（分页，自动应用数据权限和字段权限）
    
    数据权限：根据用户角色自动过滤数据
    - 超级管理员：查看所有数据
    - 普通用户：根据角色配置的数据范围查看（本人/本部门/本部门及下级/全部）
    
    字段权限：根据角色配置隐藏/脱敏字段
    - 必填字段（id、title、status）不会被隐藏
    - 可选字段（content、priority等）可以根据配置隐藏
    """
    # 构建过滤条件
    filters = []
    if title:
        filters.append(Demo.title.ilike(f"%{title}%"))
    if status is not None:
        filters.append(Demo.status == status)
    if priority is not None:
        filters.append(Demo.priority == priority)
    
    # 应用行权限（数据权限）- 自动根据用户角色过滤数据
    items, total = await DemoService.get_list_with_data_scope(
        db=db,
        page=page,
        page_size=page_size,
        filters=filters
    )
    
    # 转换为响应格式
    response_items = [DemoResponse.model_validate(item) for item in items]
    
    # 应用列权限（字段权限）- 自动从上下文获取角色并过滤字段
    response_dicts = [item.model_dump() for item in response_items]
    filtered_items = await DemoService.apply_field_permissions_auto(
        data=response_dicts,
        db=db
    )
    
    return PaginatedResponse(items=filtered_items, total=total)


@router.get("/export/excel", summary="导出Excel")
async def export_excel(db: AsyncSession = Depends(get_db)):
    """
    导出Demo数据到Excel（自动应用数据权限）
    
    只导出当前用户有权限查看的数据
    """
    output = await DemoService.export_to_excel_with_data_scope(
        db=db,
        data_converter=DemoService._export_converter
    )
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=demo_export.xlsx"}
    )


@router.get("/import/template", summary="下载导入模板")
async def download_template():
    """
    下载Excel导入模板
    """
    output = DemoService.get_import_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=demo_template.xlsx"}
    )


@router.post("/import/excel", response_model=ResponseModel, summary="导入Excel")
async def import_excel(
    file: UploadFile = File(..., description="Excel文件(.xlsx)"),
    db: AsyncSession = Depends(get_db)
):
    """
    从Excel导入Demo数据
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持.xlsx格式的Excel文件")
    
    content = await file.read()
    success_count, fail_count = await DemoService.import_from_excel(db, content)
    
    return ResponseModel(
        message=f"导入完成，成功{success_count}条，失败{fail_count}条",
        data={"success": success_count, "fail": fail_count}
    )


@router.get("/check/unique", response_model=ResponseModel, summary="检查字段唯一性")
async def check_unique(
    field: str = Query(..., description="字段名，如title"),
    value: str = Query(..., description="字段值"),
    exclude_id: str = Query(default=None, alias="excludeId", description="排除的记录ID（更新时使用）"),
    db: AsyncSession = Depends(get_db)
):
    """
    检查字段值是否唯一
    - **field**: 字段名（如 title）
    - **value**: 要检查的值
    - **excludeId**: 更新时排除自身的ID
    
    返回: {"unique": true/false}
    """
    # 限制可检查的字段，防止恶意查询
    allowed_fields = ["title"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}，允许的字段: {allowed_fields}")
    
    is_unique = await DemoService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(
        message="字段值可用" if is_unique else "字段值已存在",
        data={"unique": is_unique}
    )


@router.get("/{demo_id}", response_model=DemoResponse, summary="获取单个Demo")
async def get_demo(demo_id: str, db: AsyncSession = Depends(get_db)):
    """
    根据Demo ID获取Demo详情（应用字段权限）
    
    字段权限：根据角色配置隐藏/脱敏字段
    """
    db_demo = await DemoService.get_by_id(db, record_id=demo_id)
    if db_demo is None:
        raise HTTPException(status_code=404, detail="Demo不存在")
    
    # 转换为响应格式
    response = DemoResponse.model_validate(db_demo)
    
    # 应用列权限（字段权限）
    response_dict = response.model_dump()
    filtered_data = await DemoService.apply_field_permissions_auto(
        data=response_dict,
        db=db
    )
    
    return filtered_data


@router.put("/{demo_id}", response_model=DemoResponse, summary="全量更新Demo")
async def update_demo(demo_id: str, demo: DemoUpdate, db: AsyncSession = Depends(get_db)):
    """
    全量更新Demo信息
    """
    # 检查标题唯一性（排除自身）
    if demo.title and not await DemoService.check_unique(db, field="title", value=demo.title, exclude_id=demo_id):
        raise HTTPException(status_code=400, detail="标题已存在")
    
    db_demo = await DemoService.update(db, record_id=demo_id, data=demo)
    if db_demo is None:
        raise HTTPException(status_code=404, detail="Demo不存在")
    return db_demo


@router.patch("/{demo_id}", response_model=DemoResponse, summary="部分更新Demo")
async def patch_demo(demo_id: str, demo: DemoUpdate, db: AsyncSession = Depends(get_db)):
    """
    部分更新Demo信息（只更新传入的字段）
    """
    # 检查标题唯一性（排除自身）
    if demo.title and not await DemoService.check_unique(db, field="title", value=demo.title, exclude_id=demo_id):
        raise HTTPException(status_code=400, detail="标题已存在")
    
    db_demo = await DemoService.update(db, record_id=demo_id, data=demo)
    if db_demo is None:
        raise HTTPException(status_code=404, detail="Demo不存在")
    return db_demo


@router.delete("/{demo_id}", response_model=ResponseModel, summary="删除Demo")
async def delete_demo(
    demo_id: str,
    hard: bool = Query(default=False, description="是否物理删除，False为逻辑删除，True为物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """
    删除Demo
    - **hard=false**: 逻辑删除（默认）
    - **hard=true**: 物理删除
    """
    success = await DemoService.delete(db, record_id=demo_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="Demo不存在")
    return ResponseModel(message="删除成功")
