#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DictItem API - 字典项管理接口
提供字典项的 CRUD 操作
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.dict_item.model import DictItem
from core.dict_item.schema import (
    DictItemCreate, DictItemUpdate, DictItemResponse, DictItemSimple,
    DictItemBatchDeleteIn, DictItemBatchDeleteOut,
    DictItemBatchUpdateStatusIn, DictItemBatchUpdateStatusOut,
    DictItemSearchRequest
)
from core.dict_item.service import DictItemService

router = APIRouter(prefix="/dict_item", tags=["字典项管理"])


async def _build_dict_item_response(db: AsyncSession, item: DictItem) -> DictItemResponse:
    """构建字典项响应"""
    dict_code = None
    dict_name = None
    
    if item.dict_id:
        from core.dict.service import DictService
        dict_obj = await DictService.get_by_id(db, item.dict_id)
        if dict_obj:
            dict_code = dict_obj.code
            dict_name = dict_obj.name
    
    return DictItemResponse(
        id=item.id,
        dict_id=item.dict_id,
        dict_code=dict_code,
        dict_name=dict_name,
        label=item.label,
        value=item.value,
        icon=item.icon,
        status=item.status,
        remark=item.remark,
        sort=item.sort,
        is_deleted=item.is_deleted,
        sys_create_datetime=item.sys_create_datetime,
        sys_update_datetime=item.sys_update_datetime,
    )


@router.post("", response_model=DictItemResponse, summary="创建字典项")
async def create_dict_item(data: DictItemCreate, db: AsyncSession = Depends(get_db)):
    """创建字典项"""
    # 验证字典是否存在
    from core.dict.service import DictService
    dict_obj = await DictService.get_by_id(db, data.dict_id)
    if not dict_obj:
        raise HTTPException(status_code=400, detail=f"字典不存在: {data.dict_id}")
    
    item = await DictItemService.create(db=db, data=data)
    return await _build_dict_item_response(db, item)


@router.get("/all", response_model=List[DictItemSimple], summary="获取所有字典项（简化版）")
async def get_all_dict_items(db: AsyncSession = Depends(get_db)):
    """获取所有启用的字典项（用于选择器）"""
    items = await DictItemService.get_all_active(db)
    return items


@router.get("", response_model=PaginatedResponse[DictItemResponse], summary="获取字典项列表")
async def get_dict_item_list(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    dict_id: Optional[str] = Query(default=None, alias="dict_id", description="字典ID"),
    label: Optional[str] = Query(default=None, description="显示名称"),
    value: Optional[str] = Query(default=None, description="实际值"),
    status: Optional[bool] = Query(default=None, description="状态"),
    db: AsyncSession = Depends(get_db)
):
    """获取字典项列表（分页）"""
    filters = []
    if dict_id:
        filters.append(DictItem.dict_id == dict_id)
    if label:
        filters.append(DictItem.label.ilike(f"%{label}%"))
    if value:
        filters.append(DictItem.value.ilike(f"%{value}%"))
    if status is not None:
        filters.append(DictItem.status == status)
    
    items, total = await DictItemService.get_list(db, page=page, page_size=page_size, filters=filters)
    response_items = [await _build_dict_item_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.post("/batch/delete", response_model=DictItemBatchDeleteOut, summary="批量删除字典项")
async def batch_delete_dict_items(
    data: DictItemBatchDeleteIn,
    db: AsyncSession = Depends(get_db)
):
    """批量删除字典项"""
    count, failed_ids = await DictItemService.batch_delete(db, data.ids)
    return DictItemBatchDeleteOut(count=count, failed_ids=failed_ids)


@router.post("/batch/update_status", response_model=DictItemBatchUpdateStatusOut, summary="批量更新字典项状态")
async def batch_update_dict_item_status(
    data: DictItemBatchUpdateStatusIn,
    db: AsyncSession = Depends(get_db)
):
    """批量更新字典项状态"""
    count = await DictItemService.batch_update_status(db, data.ids, data.status)
    return DictItemBatchUpdateStatusOut(count=count)


@router.post("/search", response_model=PaginatedResponse[DictItemResponse], summary="搜索字典项")
async def search_dict_items(
    data: DictItemSearchRequest,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize", description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """搜索字典项"""
    items, total = await DictItemService.search(db, data.keyword, page, page_size)
    response_items = [await _build_dict_item_response(db, item) for item in items]
    return PaginatedResponse(items=response_items, total=total)


@router.get("/by/dict_id/{dict_id}", response_model=List[DictItemSimple], summary="根据字典ID获取字典项")
async def get_dict_items_by_dict_id(dict_id: str, db: AsyncSession = Depends(get_db)):
    """根据字典ID获取字典项列表"""
    items = await DictItemService.get_by_dict_id(db, dict_id)
    return items


@router.get("/by/dict_code/{dict_code}", response_model=List[DictItemSimple], summary="根据字典编码获取字典项")
async def get_dict_items_by_dict_code(dict_code: str, db: AsyncSession = Depends(get_db)):
    """根据字典编码获取字典项列表"""
    items = await DictItemService.get_by_dict_code(db, dict_code)
    if not items:
        # 检查字典是否存在
        from core.dict.service import DictService
        dict_obj = await DictService.get_by_code(db, dict_code)
        if not dict_obj:
            raise HTTPException(status_code=404, detail=f"字典编码不存在: {dict_code}")
    return items


@router.get("/export/excel", summary="导出字典项Excel")
async def export_dict_item_excel(db: AsyncSession = Depends(get_db)):
    """导出字典项到Excel"""
    output = await DictItemService.export_to_excel(db)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dict_item_export.xlsx"}
    )


@router.get("/import/template", summary="下载字典项导入模板")
async def download_dict_item_template():
    """下载字典项导入模板"""
    output = DictItemService.get_import_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=dict_item_template.xlsx"}
    )


@router.post("/import/excel", response_model=ResponseModel, summary="导入字典项Excel")
async def import_dict_item_excel(
    file: UploadFile = File(..., description="Excel文件(.xlsx)"),
    db: AsyncSession = Depends(get_db)
):
    """从Excel导入字典项"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持.xlsx格式")
    
    content = await file.read()
    success, fail = await DictItemService.import_from_excel(db, content)
    return ResponseModel(message=f"成功{success}条，失败{fail}条", data={"success": success, "fail": fail})


@router.get("/{item_id}", response_model=DictItemResponse, summary="获取字典项详情")
async def get_dict_item_by_id(item_id: str, db: AsyncSession = Depends(get_db)):
    """获取字典项详情"""
    item = await DictItemService.get_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="字典项不存在")
    return await _build_dict_item_response(db, item)


@router.put("/{item_id}", response_model=DictItemResponse, summary="更新字典项")
async def update_dict_item(item_id: str, data: DictItemUpdate, db: AsyncSession = Depends(get_db)):
    """更新字典项"""
    # 验证字典是否存在
    if data.dict_id:
        from core.dict.service import DictService
        dict_obj = await DictService.get_by_id(db, data.dict_id)
        if not dict_obj:
            raise HTTPException(status_code=400, detail=f"字典不存在: {data.dict_id}")
    
    item = await DictItemService.update(db, record_id=item_id, data=data)
    if item is None:
        raise HTTPException(status_code=404, detail="字典项不存在")
    return await _build_dict_item_response(db, item)


@router.delete("/{item_id}", response_model=ResponseModel, summary="删除字典项")
async def delete_dict_item(
    item_id: str,
    hard: bool = Query(default=False, description="是否物理删除"),
    db: AsyncSession = Depends(get_db)
):
    """删除字典项"""
    success = await DictItemService.delete(db, record_id=item_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="字典项不存在")
    return ResponseModel(message="删除成功")
