#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单管理 API（异步版本）
表单元数据的 CRUD、发布、复制、导入导出
"""
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import PaginatedResponse, ResponseModel
from online_dev.form_manager.schema import (
    FormImportIn,
    FormMetaCreateIn,
    FormMetaListOut,
    FormMetaOut,
    FormMetaUpdateIn,
    FormPublishIn,
    FormSubTableOut,
)
from online_dev.form_manager.service import FormService, FormServiceException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/form", tags=["表单管理"])


# ============ 辅助函数 ============

def _format_datetime(dt) -> str:
    """格式化日期时间"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return ""


async def _build_form_out(db: AsyncSession, form) -> dict:
    """构建表单详情输出"""
    sub_tables = await FormService.get_sub_tables(db, form.id)
    return {
        "id": str(form.id),
        "application_id": form.application_id,
        "name": form.name,
        "code": form.code,
        "form_type": form.form_type,
        "description": form.description or "",
        "status": form.status,
        "version": form.version,
        "db_config": form.db_config,
        "main_table": form.main_table,
        "main_table_schema": form.main_table_schema or "",
        "main_table_database": form.main_table_database or "",
        "form_config": form.form_config or {},
        "list_config": form.list_config or {},
        "sort": form.sort or 0,
        "show_in_mobile": form.show_in_mobile or False,
        "icon": form.icon or "",
        "icon_bg_color": form.icon_bg_color or "",
        "sys_create_datetime": _format_datetime(form.sys_create_datetime),
        "sys_update_datetime": _format_datetime(form.sys_update_datetime),
        "sub_tables": [
            {
                "id": str(sub.id),
                "table_name": sub.table_name,
                "table_schema": sub.table_schema or "",
                "table_database": sub.table_database or "",
                "alias": sub.alias or "",
                "foreign_key": sub.foreign_key,
                "related_field": sub.related_field or "id",
                "relation_type": sub.relation_type or "one-to-many",
                "sort": sub.sort or 0,
            }
            for sub in sub_tables
        ],
    }


def _build_form_list_out(form, application_name: str = None, application_code: str = "") -> dict:
    """构建表单列表输出"""
    return {
        "id": str(form.id),
        "application_id": form.application_id,
        "application_name": application_name or "主应用",
        "application_code": application_code or "",
        "name": form.name,
        "code": form.code,
        "form_type": form.form_type,
        "description": form.description or "",
        "status": form.status,
        "version": form.version,
        "main_table": form.main_table,
        "sort": form.sort or 0,
        "sys_create_datetime": _format_datetime(form.sys_create_datetime),
        "sys_update_datetime": _format_datetime(form.sys_update_datetime),
    }


# ============ 表单元数据 CRUD ============

@router.get("/list", response_model=PaginatedResponse[FormMetaListOut], summary="表单列表")
async def list_forms(
        application_id: str = Query(None, alias="applicationId", description="所属应用ID"),
        name: str = Query(None, description="表单名称"),
        code: str = Query(None, description="表单编码"),
        form_type: str = Query(None, alias="formType", description="表单类型"),
        status: str = Query(None, description="状态"),
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
        db: AsyncSession = Depends(get_db),
):
    """分页查询表单列表（自动应用数据权限）"""
    result = await FormService.list_with_data_scope(
        db=db,
        page=page,
        page_size=page_size,
        application_id=application_id,
        name=name,
        code=code,
        form_type=form_type,
        status=status
    )

    return PaginatedResponse(
        items=[_build_form_list_out(
            item,
            getattr(item, 'application_name', '主应用'),
            getattr(item, 'application_code', ''),
        ) for item in result["items"]],
        total=result["total"],
    )


@router.get("/form-types", summary="获取表单类型列表")
async def get_form_types():
    """获取所有表单类型"""
    return FormService.get_form_types()


@router.get("/published/simple", summary="获取已发布表单简单列表")
async def get_published_forms_simple(
        application_id: str = Query(None, alias="applicationId", description="所属应用ID"),
        all_apps: bool = Query(False, alias="allApps", description="是否返回所有应用的表单（移动端工作台使用）"),
        db: AsyncSession = Depends(get_db),
):
    """
    获取已发布表单的简单列表（用于下拉选择）
    返回格式: [{code, name, mainTable, application_id, application_name, fields: [{field, label, type}]}]
    """
    try:
        return await FormService.get_published_forms_simple(db, application_id=application_id, all_apps=all_apps)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{form_id}", response_model=FormMetaOut, summary="表单详情")
async def get_form(
        form_id: str,
        db: AsyncSession = Depends(get_db),
):
    """获取表单详情"""
    try:
        form = await FormService.get(db, form_id)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/code/{code}", response_model=FormMetaOut, summary="根据编码获取表单")
async def get_form_by_code(
        code: str,
        db: AsyncSession = Depends(get_db),
):
    """根据编码获取表单详情"""
    try:
        form = await FormService.get_by_code(db, code)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("", response_model=FormMetaOut, summary="创建表单")
async def create_form(
        request: Request,
        data: FormMetaCreateIn,
        db: AsyncSession = Depends(get_db),
):
    """创建表单"""
    user_id = request.state.user_id

    try:
        form = await FormService.create(db, data.model_dump(), user_id)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{form_id}", response_model=FormMetaOut, summary="更新表单")
async def update_form(
        request: Request,
        form_id: str,
        data: FormMetaUpdateIn,
        db: AsyncSession = Depends(get_db),
):
    """更新表单"""
    user_id = request.state.user_id

    try:
        form = await FormService.update(db, form_id, data.model_dump(exclude_none=True), user_id)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/batch/delete", response_model=dict, summary="批量删除表单")
async def batch_delete_forms(
        ids: List[str] = Query(..., description="表单ID列表"),
        db: AsyncSession = Depends(get_db),
):
    """批量删除表单"""
    count = await FormService.batch_delete(db, ids)
    return {"count": count}


@router.delete("/{form_id}", response_model=FormMetaOut, summary="删除表单")
async def delete_form(
        form_id: str,
        db: AsyncSession = Depends(get_db),
):
    """删除表单"""
    try:
        form = await FormService.get(db, form_id)
        form_out = await _build_form_out(db, form)
        await FormService.delete(db, form_id)
        return form_out
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 发布/取消发布 ============

@router.post("/{form_id}/publish", response_model=FormMetaOut, summary="发布表单")
async def publish_form(
        form_id: str,
        data: FormPublishIn,
        db: AsyncSession = Depends(get_db),
):
    """发布表单并创建菜单"""
    try:
        form = await FormService.publish(db, form_id, data.model_dump())
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{form_id}/unpublish", response_model=FormMetaOut, summary="取消发布")
async def unpublish_form(
        form_id: str,
        db: AsyncSession = Depends(get_db),
):
    """取消发布表单并删除菜单"""
    try:
        form = await FormService.unpublish(db, form_id)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 复制 ============

@router.post("/{form_id}/copy", response_model=FormMetaOut, summary="复制表单")
async def copy_form(
        request: Request,
        form_id: str,
        new_code: str = Query(..., alias="new_code", description="新表单编码"),
        new_name: str = Query(None, alias="new_name", description="新表单名称"),
        db: AsyncSession = Depends(get_db),
):
    """复制表单"""
    user_id = request.state.user_id

    try:
        form = await FormService.copy(db, form_id, new_code, new_name, user_id)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 导入/导出配置 ============

@router.get("/{form_id}/export", summary="导出表单配置")
async def export_form_config(
        form_id: str,
        db: AsyncSession = Depends(get_db),
):
    """导出表单配置为 JSON"""
    try:
        config = await FormService.export_config(db, form_id)

        # 返回 JSON 文件
        content = json.dumps(config, ensure_ascii=False, indent=2)

        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{config["code"]}.json"'
            }
        )
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import", response_model=FormMetaOut, summary="导入表单配置")
async def import_form_config(
        request: Request,
        data: FormImportIn,
        db: AsyncSession = Depends(get_db),
):
    """导入表单配置"""
    user_id = request.state.user_id

    try:
        form = await FormService.import_config(db, data.model_dump(), user_id)
        return await _build_form_out(db, form)
    except FormServiceException as e:
        raise HTTPException(status_code=400, detail=str(e))
