#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dict API - 字典管理接口
提供字典的 CRUD 操作
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.application.model import Application
from core.dict.model import Dict
from core.dict.schema import (
    DictCreate, DictUpdate, DictResponse, DictSimple,
    DictBatchDeleteIn, DictBatchDeleteOut,
    DictBatchUpdateStatusIn, DictBatchUpdateStatusOut,
    DictSearchRequest
)
from core.dict.service import DictService

router = APIRouter(prefix="/dict", tags=["字典管理"])


@router.post("", response_model=DictResponse, summary="创建字典")
async def create_dict(data: DictCreate, db: AsyncSession = Depends(get_db)):
    """创建字典"""
    # 唯一性校验
    if not await DictService.check_unique(db, field="code", value=data.code):
        raise HTTPException(status_code=400, detail=f"字典编码已存在: {data.code}")
    
    dict_obj = await DictService.create(db=db, data=data)
    return dict_obj


@router.get("/all", response_model=List[DictSimple], summary="获取所有字典（简化版）")
async def get_all_dicts(
    application_id: str = Query(None, alias="applicationId", description="所属应用ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有启用的字典（用于选择器）"""
    dicts = await DictService.get_all_active(db, application_id=application_id)
    return dicts


@router.get("", response_model=PaginatedResponse[DictResponse], summary="获取字典列表")
async def get_dict_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    application_id: str = Query(None, alias="applicationId", description="所属应用ID"),
    name: Optional[str] = Query(default=None, description="字典名称"),
    code: Optional[str] = Query(default=None, description="字典编码"),
    status: Optional[bool] = Query(default=None, description="状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取字典列表（分页，自动应用数据权限）"""
    filters = []
    # 应用过滤（同时包含全局可见的字典）
    if application_id:
        filters.append(or_(
            Dict.application_id == application_id,
            Dict.is_global == True  # noqa: E712
        ))
    else:
        filters.append(or_(
            Dict.application_id.is_(None),
            Dict.is_global == True  # noqa: E712
        ))
    if name:
        filters.append(Dict.name.ilike(f"%{name}%"))
    if code:
        filters.append(Dict.code.ilike(f"%{code}%"))
    if status is not None:
        filters.append(Dict.status == status)
    
    # 使用带数据权限的列表查询
    items, total = await DictService.get_list_with_data_scope(db, page=page, page_size=page_size, filters=filters)
    
    # 批量查询应用名称
    app_ids = list({item.application_id for item in items if item.application_id})
    app_name_map = {}
    if app_ids:
        app_result = await db.execute(
            select(Application.id, Application.name).where(Application.id.in_(app_ids))
        )
        app_name_map = {row.id: row.name for row in app_result}
    
    for item in items:
        item.application_name = app_name_map.get(item.application_id, "")
    
    return PaginatedResponse(items=items, total=total)


@router.post("/batch/delete", response_model=DictBatchDeleteOut, summary="批量删除字典")
async def batch_delete_dicts(
    data: DictBatchDeleteIn,
    db: AsyncSession = Depends(get_db)
):
    """批量删除字典"""
    count, failed_ids = await DictService.batch_delete(db, data.ids)
    return DictBatchDeleteOut(count=count, failed_ids=failed_ids)


@router.post("/batch/update_status", response_model=DictBatchUpdateStatusOut, summary="批量更新字典状态")
async def batch_update_dict_status(
    data: DictBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量更新字典状态"""
    count = await DictService.batch_update_status(db, data.ids, data.status)
    return DictBatchUpdateStatusOut(count=count)


@router.post("/search", response_model=PaginatedResponse[DictResponse], summary="搜索字典")
async def search_dicts(
    data: DictSearchRequest,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """搜索字典"""
    items, total = await DictService.search(db, data.keyword, page, page_size)
    return PaginatedResponse(items=items, total=total)


@router.get("/export/excel", summary="导出字典Excel")
async def export_dict_excel(db: AsyncSession = Depends(get_db)):
    """导出字典到Excel"""
    output = await DictService.export_to_excel(db)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dict_export.xlsx"}
    )


@router.get("/import/template", summary="下载字典导入模板")
async def download_dict_template():
    """下载字典导入模板"""
    output = DictService.get_import_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dict_template.xlsx"}
    )


@router.post("/import/excel", response_model=ResponseModel, summary="导入字典Excel")
async def import_dict_excel(
    file: UploadFile = File(..., description="Excel文件(.xlsx)"),
    db: AsyncSession = Depends(get_db)
):
    """从Excel导入字典"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持.xlsx格式")
    
    content = await file.read()
    success, fail = await DictService.import_from_excel(db, content)
    return ResponseModel(message=f"成功{success}条，失败{fail}条", data={"success": success, "fail": fail})


@router.get("/check/unique", response_model=ResponseModel, summary="检查字典唯一性")
async def check_dict_unique(
    field: str = Query(..., description="字段名"),
    value: str = Query(..., description="字段值"),
    exclude_id: str = Query(default=None, alias="excludeId", description="排除ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查字典字段唯一性"""
    allowed_fields = ["code"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")
    
    is_unique = await DictService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.get("/by/code/{code}", response_model=DictResponse, summary="根据编码获取字典")
async def get_dict_by_code(code: str, db: AsyncSession = Depends(get_db)):
    """根据编码获取字典"""
    dict_obj = await DictService.get_by_code(db, code)
    if dict_obj is None:
        raise HTTPException(status_code=404, detail=f"字典编码不存在: {code}")
    return dict_obj


@router.get("/{dict_id}", response_model=DictResponse, summary="获取字典详情")
async def get_dict_by_id(dict_id: str, db: AsyncSession = Depends(get_db)):
    """获取字典详情"""
    dict_obj = await DictService.get_by_id(db, dict_id)
    if dict_obj is None:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dict_obj


@router.put("/{dict_id}", response_model=DictResponse, summary="更新字典")
async def update_dict(dict_id: str, data: DictUpdate, db: AsyncSession = Depends(get_db)):
    """更新字典"""
    # 唯一性校验（排除自身）
    if data.code and not await DictService.check_unique(db, field="code", value=data.code, exclude_id=dict_id):
        raise HTTPException(status_code=400, detail=f"字典编码已存在: {data.code}")
    
    dict_obj = await DictService.update(db, record_id=dict_id, data=data)
    if dict_obj is None:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dict_obj


@router.delete("/{dict_id}", response_model=ResponseModel, summary="删除字典")
async def delete_dict(
    dict_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除字典"""
    success = await DictService.delete(db, record_id=dict_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="字典不存在")
    return ResponseModel(message="删除成功")
