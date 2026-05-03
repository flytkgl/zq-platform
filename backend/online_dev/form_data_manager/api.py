#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单数据操作 API（异步版本）
动态操作表单数据，支持主表和子表的 CRUD
支持操作权限和数据权限控制
"""
import asyncio
import json
import logging
import tempfile
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    DBAPIError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
)

from app.database import get_db
from online_dev.form_data_manager.schema import (
    FormDataCreateIn,
    FormDataListOut,
    FormDataUpdateIn,
)
from online_dev.form_data_manager.service import (
    FormDataException, FormDataService,
    MAX_IMPORT_EXPORT_ROWS, SERVER_MEMORY_GB,
)
from online_dev.form_data_manager.dependencies import (
    check_form_permission,
    get_user_form_permissions,
    get_data_scope_filter,
    get_user_info,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/form-data", tags=["表单数据"])


def _handle_db_error(e: Exception) -> HTTPException:
    """将数据库异常转换为前端友好的 HTTP 错误响应"""
    error_msg = str(e)
    logger.error(f"数据库操作错误: {error_msg}", exc_info=True)

    # 列不存在
    if "UndefinedColumnError" in error_msg or "column" in error_msg.lower() and "does not exist" in error_msg.lower():
        # 提取列名
        import re
        col_match = re.search(r'column ["\']?([\w.]+)["\']?', error_msg, re.IGNORECASE)
        col_name = col_match.group(1) if col_match else '未知'
        return HTTPException(status_code=400, detail=f"数据库字段 '{col_name}' 不存在，请检查表单配置与数据库表结构是否一致")

    # 表不存在
    if "UndefinedTableError" in error_msg or ("relation" in error_msg.lower() and "does not exist" in error_msg.lower()):
        import re
        tbl_match = re.search(r'relation ["\']?([\w."]+)["\']?', error_msg, re.IGNORECASE)
        tbl_name = tbl_match.group(1) if tbl_match else '未知'
        return HTTPException(status_code=400, detail=f"数据库表 {tbl_name} 不存在，请检查数据源配置")

    # 唯一约束冲突
    if isinstance(e, IntegrityError) or "UniqueViolation" in error_msg or "duplicate key" in error_msg.lower():
        return HTTPException(status_code=400, detail="数据重复，违反唯一约束，请检查是否存在重复数据")

    # 非空约束
    if "NotNullViolation" in error_msg or "null value in column" in error_msg.lower():
        import re
        col_match = re.search(r'column ["\']?([\w]+)["\']?', error_msg, re.IGNORECASE)
        col_name = col_match.group(1) if col_match else '未知'
        return HTTPException(status_code=400, detail=f"字段 '{col_name}' 不能为空")

    # 数据类型错误
    if "InvalidTextRepresentation" in error_msg or "invalid input syntax" in error_msg.lower():
        return HTTPException(status_code=400, detail="数据类型不匹配，请检查输入数据格式")

    # 连接错误
    if isinstance(e, OperationalError) or "connection" in error_msg.lower():
        return HTTPException(status_code=503, detail="数据库连接异常，请稍后重试")

    # SQL 语法错误
    if isinstance(e, ProgrammingError):
        return HTTPException(status_code=400, detail="数据库查询异常，请检查表单配置是否正确")

    # MissingGreenlet（异步上下文问题）
    if "MissingGreenlet" in error_msg:
        return HTTPException(status_code=500, detail="服务器内部错误，请刷新页面重试")

    # 其他数据库错误
    if isinstance(e, DBAPIError):
        return HTTPException(status_code=500, detail="数据库操作失败，请联系管理员")

    # 未知错误
    return HTTPException(status_code=500, detail=f"操作失败: {error_msg[:200]}")


# ============ 权限查询 ============

@router.get("/{form_code}/permissions", summary="获取当前用户的表单权限")
async def get_form_permissions(
        form_code: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户对该表单的操作权限
    
    返回格式:
    {
        "view": true,
        "add": true,
        "edit": true,
        "delete": false,
        "export": true,
        "import": false
    }
    """
    return await get_user_form_permissions(form_code, request, db)


@router.get("/{form_code}/field-permissions", summary="获取当前用户的字段权限")
async def get_field_permissions(
        form_code: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户对该表单的字段权限
    
    返回格式:
    {
        "field_name": {
            "permission_type": "read" | "write" | "hidden" | "masked",
            "mask_rule": "phone" | "email" | "id_card" | "name" | null
        },
        ...
    }
    """
    from core.resource_scope.field_permission.service import ResourceFieldPermissionService
    
    # 获取用户信息
    user_info = await get_user_info(request)
    if not user_info or not user_info.get('role_ids'):
        return {}
    
    role_ids = user_info['role_ids']
    resource_type = f"form:{form_code}"
    
    # 获取字段权限配置
    configs = await ResourceFieldPermissionService.get_by_roles_and_resource(
        db, role_ids, resource_type
    )
    
    if not configs:
        return {}
    
    # 合并权限
    merged_perms = await ResourceFieldPermissionService.merge_field_permissions(
        configs, "most_permissive"
    )
    
    return merged_perms or {}


# ============ 表单数据 CRUD ============

@router.get("/{form_code}/list", response_model=FormDataListOut, summary="查询表单数据列表")
async def list_form_data(
        request: Request,
        form_code: str,
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, alias="pageSize", description="每页条数"),
        sort_fields: str = Query(None, alias="sortFields", description="排序字段（多个用逗号分隔）"),
        sort_orders: str = Query(None, alias="sortOrders", description="排序方向（多个用逗号分隔）"),
        search: str = Query(None, description="搜索关键词"),
        search_fields: str = Query(None, alias="search_fields", description="搜索字段（多个用逗号分隔）"),
        db: AsyncSession = Depends(get_db),
):
    """查询表单数据列表（带数据权限过滤）"""
    import time
    _api_t0 = time.perf_counter()

    # 权限校验：查看权限
    await check_form_permission(form_code, "view", request, db)

    _api_t1 = time.perf_counter()
    logger.info(f"[API list 耗时] 权限校验: {(_api_t1 - _api_t0) * 1000:.1f}ms")

    # 从查询参数中提取过滤条件
    filters = {}
    # 临时存储 gte 和 lte 条件，用于后续合并
    range_conditions = {}
    
    for key, value in request.query_params.items():
        if key not in ("page", "pageSize", "sortFields", "sortOrders", "search", "search_fields") and value:
            # 支持 filter_field 格式（多选过滤，值用逗号分隔）
            if key.startswith("filter_"):
                field = key[7:]  # 去掉 "filter_" 前缀
                filter_values = [v.strip() for v in value.split(',') if v.strip()]
                if filter_values:
                    filters[field] = {"type": "in", "value": filter_values}
            # 支持 field__type 格式，如 name__like, name__gte, name__lte
            elif "__" in key:
                field, filter_type = key.rsplit("__", 1)
                # case_sensitive 是字段过滤的修饰符，合并到已有过滤条件中
                if filter_type == "case_sensitive":
                    if field in filters and isinstance(filters[field], dict):
                        filters[field]["case_sensitive"] = value.lower() in ("true", "1")
                    continue
                # 收集 gte 和 lte 条件，稍后合并
                if filter_type in ("gte", "lte"):
                    if field not in range_conditions:
                        range_conditions[field] = {}
                    range_conditions[field][filter_type] = value
                else:
                    filters[field] = {"type": filter_type, "value": value}
            else:
                filters[key] = value
    
    # 合并 gte 和 lte 条件为 range 查询
    for field, conditions in range_conditions.items():
        if "gte" in conditions and "lte" in conditions:
            # 同时有 gte 和 lte，合并为 range
            filters[field] = {"type": "range", "value": [conditions["gte"], conditions["lte"]]}
        elif "gte" in conditions:
            filters[field] = {"type": "gte", "value": conditions["gte"]}
        elif "lte" in conditions:
            filters[field] = {"type": "lte", "value": conditions["lte"]}

    # 解析多字段排序
    sort_list = []
    if sort_fields:
        fields = [f.strip() for f in sort_fields.split(',') if f.strip()]
        orders = [o.strip() for o in sort_orders.split(',')] if sort_orders else []
        
        for i, field in enumerate(fields):
            order = orders[i] if i < len(orders) else 'desc'
            sort_list.append({'field': field, 'order': order})

    # 获取数据权限过滤条件
    data_scope = await get_data_scope_filter(form_code, request, db)

    _api_t2 = time.perf_counter()
    logger.info(f"[API list 耗时] 数据权限配置获取: {(_api_t2 - _api_t1) * 1000:.1f}ms")

    # 获取用户信息
    user_info = await get_user_info(request)

    # 解析搜索字段
    search_field_list = None
    if search and search_fields:
        search_field_list = [f.strip() for f in search_fields.split(',') if f.strip()]

    try:
        service = await FormDataService.create_service(db, form_code)

        _api_t3 = time.perf_counter()
        logger.info(f"[API list 耗时] create_service: {(_api_t3 - _api_t2) * 1000:.1f}ms")

        result = await service.list(
            db=db,
            page=page,
            page_size=page_size,
            filters=filters if filters else None,
            sort_list=sort_list if sort_list else None,
            data_scope=data_scope,
            search=search,
            search_fields=search_field_list
        )

        _api_t4 = time.perf_counter()
        logger.info(f"[API list 耗时] ===== API 总耗时: {(_api_t4 - _api_t0) * 1000:.1f}ms (form={form_code}, page={page}) =====")

        return result
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.get("/{form_code}/tree/children", summary="获取树形子节点（懒加载）")
async def get_tree_children(
        form_code: str,
        request: Request,
        parent_id: str = Query(None, alias="parentId", description="父节点ID，为空获取根节点"),
        parent_field: str = Query("parent_id", alias="parentField", description="父节点字段名"),
        db: AsyncSession = Depends(get_db),
):
    """
    获取树形数据的子节点（用于懒加载模式）
    - parent_id 为空时获取根节点（parent_field 为空或 NULL 的记录）
    - parent_id 有值时获取指定父节点的子节点
    """
    # 权限校验：查看权限
    await check_form_permission(form_code, "view", request, db)

    # 获取数据权限
    data_scope = await get_data_scope_filter(form_code, request, db)

    try:
        service = await FormDataService.create_service(db, form_code)
        return await service.get_tree_children(
            db=db,
            parent_id=parent_id,
            parent_field=parent_field,
            data_scope=data_scope
        )
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.get("/{form_code}/field-values/{field_name}", summary="获取字段唯一值列表")
async def get_field_values(
        form_code: str,
        field_name: str,
        page: int = Query(1, description="页码"),
        page_size: int = Query(20, alias="pageSize", description="每页条数"),
        search: str = Query(None, description="搜索关键词"),
        db: AsyncSession = Depends(get_db),
):
    """获取指定字段的唯一值列表（用于过滤选项）"""
    try:
        service = await FormDataService.create_service(db, form_code)
        return await service.get_field_values(
            db=db,
            field_name=field_name,
            page=page,
            page_size=page_size,
            search=search
        )
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.get("/{form_code}/check-unique", summary="检查字段值唯一性")
async def check_unique(
        form_code: str,
        field: str = Query(..., description="字段名"),
        value: str = Query(..., description="字段值"),
        exclude_id: str = Query(None, alias="excludeId", description="排除的记录ID（编辑时排除自身）"),
        db: AsyncSession = Depends(get_db),
):
    """检查指定字段的值在数据库中是否唯一"""
    try:
        service = await FormDataService.create_service(db, form_code)
        is_unique = await service.check_unique(
            db=db,
            field_name=field,
            value=value,
            exclude_id=exclude_id
        )
        return {"unique": is_unique}
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.get("/{form_code}/detail/{pk}", summary="获取表单数据详情")
async def get_form_data(
        form_code: str,
        pk: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """获取单条表单数据（含子表）"""
    # 权限校验：查看权限
    await check_form_permission(form_code, "view", request, db)
    
    try:
        service = await FormDataService.create_service(db, form_code)
        return await service.get(db, pk)
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.post("/{form_code}", summary="新增表单数据")
async def create_form_data(
        form_code: str,
        data: FormDataCreateIn,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """新增表单数据（含子表）"""
    # 权限校验：新增权限
    await check_form_permission(form_code, "add", request, db)
    
    try:
        service = await FormDataService.create_service(db, form_code)
        return await service.create(db, data.model_dump())
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.put("/{form_code}/{pk}", summary="更新表单数据")
async def update_form_data(
        form_code: str,
        pk: str,
        data: FormDataUpdateIn,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """更新表单数据（含子表）"""
    # 权限校验：编辑权限
    await check_form_permission(form_code, "edit", request, db)
    
    try:
        service = await FormDataService.create_service(db, form_code)
        return await service.update(db, pk, data.model_dump())
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.delete("/{form_code}/{pk}", summary="删除表单数据")
async def delete_form_data(
        form_code: str,
        pk: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """删除表单数据（含子表）"""
    # 权限校验：删除权限
    await check_form_permission(form_code, "delete", request, db)
    
    try:
        service = await FormDataService.create_service(db, form_code)
        await service.delete(db, pk)
        return {"success": True}
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.delete("/{form_code}/batch/delete", summary="批量删除表单数据")
async def batch_delete_form_data(
        form_code: str,
        request: Request,
        ids: List[str] = Query(..., description="ID列表"),
        db: AsyncSession = Depends(get_db),
):
    """批量删除表单数据"""
    # 权限校验：删除权限
    await check_form_permission(form_code, "delete", request, db)
    
    try:
        service = await FormDataService.create_service(db, form_code)
        count = await service.batch_delete(db, ids)
        return {"count": count}
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


# ============ 导入导出 ============

# 临时导出文件存储（file_id -> 文件路径）
_export_temp_files: Dict[str, Path] = {}


def _parse_export_query_params(query_params: dict) -> Tuple[
    Dict[str, Any], List[Dict[str, str]], Optional[str], Optional[List[str]]
]:
    """从前端传来的 queryParams 解析出 filters, sort_list, search, search_fields"""
    filters: Dict[str, Any] = {}
    range_conditions: Dict[str, dict] = {}
    sort_list: List[Dict[str, str]] = []
    search: Optional[str] = None
    search_fields: Optional[List[str]] = None

    for key, value in query_params.items():
        if not value and value != 0:
            continue

        if key == "sortFields":
            sort_fields_str = str(value)
            sort_orders_str = str(query_params.get("sortOrders", ""))
            fields = [f.strip() for f in sort_fields_str.split(',') if f.strip()]
            orders = [o.strip() for o in sort_orders_str.split(',')] if sort_orders_str else []
            for i, field in enumerate(fields):
                order = orders[i] if i < len(orders) else 'desc'
                sort_list.append({'field': field, 'order': order})
            continue

        if key in ("sortOrders",):
            continue

        if key == "search":
            search = str(value)
            continue

        if key == "search_fields":
            search_fields = [f.strip() for f in str(value).split(',') if f.strip()]
            continue

        if key.startswith("filter_"):
            field = key[7:]
            filter_values = [v.strip() for v in str(value).split(',') if v.strip()]
            if filter_values:
                filters[field] = {"type": "in", "value": filter_values}
        elif "__" in key:
            field, filter_type = key.rsplit("__", 1)
            # case_sensitive 是修饰符，合并到已有过滤条件中
            if filter_type == "case_sensitive":
                if field in filters and isinstance(filters[field], dict):
                    filters[field]["case_sensitive"] = str(value).lower() in ("true", "1")
                continue
            if filter_type in ("gte", "lte"):
                if field not in range_conditions:
                    range_conditions[field] = {}
                range_conditions[field][filter_type] = value
            else:
                filters[field] = {"type": filter_type, "value": value}
        else:
            filters[key] = value

    for field, conditions in range_conditions.items():
        if "gte" in conditions and "lte" in conditions:
            filters[field] = {"type": "range", "value": [conditions["gte"], conditions["lte"]]}
        elif "gte" in conditions:
            filters[field] = {"type": "gte", "value": conditions["gte"]}
        elif "lte" in conditions:
            filters[field] = {"type": "lte", "value": conditions["lte"]}

    return filters, sort_list, search, search_fields


@router.get("/import-export/config", summary="获取导入导出配置")
async def get_import_export_config():
    """返回服务器内存决定的导入导出行数上限"""
    return {
        "maxRows": MAX_IMPORT_EXPORT_ROWS,
        "serverMemoryGB": SERVER_MEMORY_GB,
    }


@router.post("/{form_code}/export/task", summary="导出表单数据到 Excel")
async def export_form_data(
        form_code: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    导出表单数据到 Excel（流式导出，支持大数据量）
    
    - 使用分批查询避免内存溢出
    - 支持字段选择和子表导出
    - 支持查询条件过滤导出（与列表查询保持一致）
    - 最大导出行数根据服务器内存动态计算
    """
    # 权限校验：导出权限
    await check_form_permission(form_code, "export", request, db)
    
    try:
        body = await request.json()
        include_sub_tables = body.get("includeSubTables", False)
        selected_fields = body.get("selectedFields", [])
        query_params = body.get("queryParams", {})
        
        if include_sub_tables and selected_fields and "id" not in selected_fields:
            selected_fields = ["id"] + selected_fields
        
        filters, sort_list, search, search_fields = _parse_export_query_params(query_params)
        
        service = await FormDataService.create_service(db, form_code)
        
        from online_dev.form_data_manager.dependencies import get_data_scope_filter
        data_scope = await get_data_scope_filter(form_code, request, db)
        
        excel_buffer = await service.export_to_excel_streaming(
            db=db,
            selected_fields=selected_fields if selected_fields else None,
            include_sub_tables=include_sub_tables,
            batch_size=1000,
            data_scope=data_scope,
            filters=filters if filters else None,
            sort_list=sort_list if sort_list else None,
            search=search,
            search_fields=search_fields
        )
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={form_code}_export.xlsx"
            }
        )
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.post("/{form_code}/export/sse", summary="SSE 导出表单数据（带进度）")
async def export_form_data_sse(
        form_code: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """
    通过 SSE 导出表单数据，实时推送导出进度。
    
    SSE 事件类型：
    - progress: {processed, total, percent} 每批处理后推送
    - completed: {fileId, total} 导出完成，返回临时文件 ID 用于下载
    - error: {message} 导出失败
    """
    await check_form_permission(form_code, "export", request, db)

    body = await request.json()
    include_sub_tables = body.get("includeSubTables", False)
    selected_fields = body.get("selectedFields", [])
    query_params = body.get("queryParams", {})

    if include_sub_tables and selected_fields and "id" not in selected_fields:
        selected_fields = ["id"] + selected_fields

    filters, sort_list, search, search_fields = _parse_export_query_params(query_params)

    from online_dev.form_data_manager.dependencies import get_data_scope_filter
    data_scope = await get_data_scope_filter(form_code, request, db)

    service = await FormDataService.create_service(db, form_code)

    progress_queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(processed: int, total: int, stage: str = "querying"):
        if stage == "generating":
            percent = 99.0
        elif total > 0:
            percent = round(processed / total * 90, 1)
        else:
            percent = 0
        await progress_queue.put(
            f"event: progress\ndata: {json.dumps({'processed': processed, 'total': total, 'percent': percent, 'stage': stage}, ensure_ascii=False)}\n\n"
        )

    async def run_export():
        try:
            logger.debug("SSE run_export 开始执行")
            excel_buffer = await service.export_to_excel_streaming(
                db=db,
                selected_fields=selected_fields if selected_fields else None,
                include_sub_tables=include_sub_tables,
                batch_size=1000,
                data_scope=data_scope,
                filters=filters if filters else None,
                sort_list=sort_list if sort_list else None,
                search=search,
                search_fields=search_fields,
                on_progress=on_progress
            )
            logger.debug("SSE export_to_excel_streaming 完成，开始写文件")

            file_id = str(uuid.uuid4())
            temp_dir = Path(tempfile.gettempdir()) / "form_export"
            temp_dir.mkdir(parents=True, exist_ok=True)
            file_path = temp_dir / f"{file_id}.xlsx"
            buffer_bytes = excel_buffer.getvalue()
            file_path.write_bytes(buffer_bytes)
            _export_temp_files[file_id] = file_path
            logger.debug(f"SSE 导出文件已保存: {file_path}, 大小: {len(buffer_bytes)} bytes")

            async def cleanup():
                await asyncio.sleep(300)
                _export_temp_files.pop(file_id, None)
                try:
                    file_path.unlink(missing_ok=True)
                except Exception:
                    pass
            asyncio.create_task(cleanup())

            completed_msg = f"event: completed\ndata: {json.dumps({'fileId': file_id, 'total': len(buffer_bytes)}, ensure_ascii=False)}\n\n"
            logger.debug(f"SSE 即将推送 completed 事件: fileId={file_id}")
            await progress_queue.put(completed_msg)
            logger.debug("SSE completed 事件已推送到队列")
        except Exception as e:
            logger.error(f"SSE 导出失败: {e}", exc_info=True)
            try:
                await progress_queue.put(
                    f"event: error\ndata: {json.dumps({'message': str(e)[:500]}, ensure_ascii=False)}\n\n"
                )
            except Exception as e2:
                logger.error(f"SSE 推送 error 事件也失败: {e2}", exc_info=True)
        finally:
            logger.debug("SSE run_export finally: 推送 None 结束信号")
            await progress_queue.put(None)

    async def event_generator():
        export_task = asyncio.ensure_future(run_export())
        try:
            while True:
                msg = await progress_queue.get()
                if msg is None:
                    break
                yield msg
        except (asyncio.CancelledError, GeneratorExit):
            export_task.cancel()
        finally:
            if not export_task.done():
                export_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/{form_code}/export/download/{file_id}", summary="下载导出的临时文件")
async def download_export_file(
        form_code: str,
        file_id: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    """下载 SSE 导出生成的临时 Excel 文件"""
    await check_form_permission(form_code, "export", request, db)

    file_path = _export_temp_files.get(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="导出文件不存在或已过期，请重新导出")

    def file_stream():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk
        # 下载完成后清理
        _export_temp_files.pop(file_id, None)
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass

    return StreamingResponse(
        file_stream(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={form_code}_export.xlsx"
        }
    )


@router.get("/{form_code}/import/template", summary="下载导入模板")
async def download_import_template(
        form_code: str,
        db: AsyncSession = Depends(get_db),
):
    """下载导入模板"""
    try:
        service = await FormDataService.create_service(db, form_code)
        template_buffer = await service.get_import_template()
        
        return StreamingResponse(
            template_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={form_code}_template.xlsx"
            }
        )
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.post("/{form_code}/import/excel", summary="从 Excel 导入数据")
async def import_form_data(
        form_code: str,
        request: Request,
        file: UploadFile = File(..., description="Excel 文件 (.xlsx)"),
        mode: str = Form(default="append", description="导入模式：append（追加）或 overwrite（覆盖）"),
        data_handling: str = Form(default="insert_only", description="数据处理方式：insert_only / update_only / upsert"),
        match_field: str = Form(default="", description="更新模式下用于匹配已有数据的字段名"),
        validate_only: bool = Form(default=False, description="是否仅验证数据，不执行实际导入"),
        db: AsyncSession = Depends(get_db),
):
    """
    从 Excel 导入数据
    
    - mode: 导入模式
      - append: 追加模式（默认），保留现有数据
      - overwrite: 覆盖模式，先清空表再导入
    - data_handling: 数据处理方式（追加模式下有效）
      - insert_only: 仅新增（默认）
      - update_only: 仅更新已有数据，不新增
      - upsert: 更新已有数据，不存在则新增
    - match_field: 更新/upsert 模式下用于匹配已有数据的字段名
    - validate_only: 仅验证模式，只检查数据是否合规，不执行实际导入
    """
    await check_form_permission(form_code, "import", request, db)
    
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持 .xlsx 格式")
    
    if mode not in ("append", "overwrite"):
        raise HTTPException(status_code=400, detail="mode 参数只能是 append 或 overwrite")
    
    if data_handling not in ("insert_only", "update_only", "upsert"):
        raise HTTPException(status_code=400, detail="data_handling 参数只能是 insert_only、update_only 或 upsert")
    
    if mode == "append" and data_handling in ("update_only", "upsert") and not match_field:
        raise HTTPException(status_code=400, detail="更新模式下必须指定 match_field")
    
    try:
        service = await FormDataService.create_service(db, form_code)
        content = await file.read()
        success, fail, errors = await service.import_from_excel(
            db, content, mode=mode, validate_only=validate_only,
            data_handling=data_handling, match_field=match_field or None
        )
        
        if validate_only:
            meta = {}
            real_errors = errors
            if errors and isinstance(errors[-1], dict) and errors[-1].get("_meta"):
                meta = errors[-1]
                real_errors = errors[:-1]
            return {
                "success": success,
                "fail": fail,
                "message": f"数据验证完成：{success} 条通过，{fail} 条失败",
                "errors": real_errors,
                "validated": True,
                "will_insert": meta.get("will_insert", success),
                "will_update": meta.get("will_update", 0),
                "action": meta.get("action", ""),
            }
        
        return {
            "success": success,
            "fail": fail,
            "message": f"成功导入 {success} 条，失败 {fail} 条",
            "errors": errors
        }
    except FormDataException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise _handle_db_error(e)


@router.post("/{form_code}/import/validate/sse", summary="SSE 验证导入数据（带进度）")
async def validate_import_data_sse(
        form_code: str,
        request: Request,
        file: UploadFile = File(..., description="Excel 文件 (.xlsx)"),
        mode: str = Form(default="append", description="导入模式：append（追加）或 overwrite（覆盖）"),
        data_handling: str = Form(default="insert_only", description="数据处理方式：insert_only / update_only / upsert"),
        match_field: str = Form(default="", description="更新模式下用于匹配已有数据的字段名"),
        db: AsyncSession = Depends(get_db),
):
    """
    通过 SSE 验证导入数据，实时推送解析进度。

    SSE 事件类型：
    - progress: {processed, total, percent, stage} 解析进度
    - completed: {success, fail, errors, validated} 验证完成
    - error: {message} 验证失败
    """
    await check_form_permission(form_code, "import", request, db)

    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持 .xlsx 格式")

    if mode not in ("append", "overwrite"):
        raise HTTPException(status_code=400, detail="mode 参数只能是 append 或 overwrite")

    if data_handling not in ("insert_only", "update_only", "upsert"):
        raise HTTPException(status_code=400, detail="data_handling 参数只能是 insert_only、update_only 或 upsert")

    if mode == "append" and data_handling in ("update_only", "upsert") and not match_field:
        raise HTTPException(status_code=400, detail="更新模式下必须指定 match_field")

    content = await file.read()
    service = await FormDataService.create_service(db, form_code)

    progress_queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(processed: int, total: int, stage: str, success: int, fail: int):
        if total > 0:
            if stage == "parsing":
                percent = round(processed / total * 60, 1)
            elif stage == "validating":
                percent = 60 + round(processed / total * 39, 1)
            else:
                percent = round(processed / total * 99, 1)
        else:
            percent = 0
        await progress_queue.put(
            f"event: progress\ndata: {json.dumps({'processed': processed, 'total': total, 'percent': percent, 'stage': stage}, ensure_ascii=False)}\n\n"
        )

    async def run_validate():
        try:
            logger.debug(f"SSE validate 开始: form_code={form_code}")
            success, fail, errors = await service.import_from_excel(
                db, content, mode=mode, validate_only=True,
                data_handling=data_handling,
                match_field=match_field or None,
                on_progress=on_progress
            )
            # 提取 _meta 信息（errors 列表末尾可能含 _meta 字典）
            meta = {}
            real_errors = errors
            if errors and isinstance(errors[-1], dict) and errors[-1].get("_meta"):
                meta = errors[-1]
                real_errors = errors[:-1]

            completed_data = {
                "success": success,
                "fail": fail,
                "errors": real_errors,
                "message": f"数据验证完成：{success} 条通过，{fail} 条失败",
                "validated": True,
                "will_insert": meta.get("will_insert", success),
                "will_update": meta.get("will_update", 0),
                "action": meta.get("action", ""),
            }
            logger.debug(f"SSE validate 完成: success={success}, fail={fail}")
            await progress_queue.put(
                f"event: completed\ndata: {json.dumps(completed_data, ensure_ascii=False)}\n\n"
            )
        except Exception as e:
            logger.error(f"SSE 验证失败: {e}", exc_info=True)
            try:
                await progress_queue.put(
                    f"event: error\ndata: {json.dumps({'message': str(e)[:500]}, ensure_ascii=False)}\n\n"
                )
            except Exception as e2:
                logger.error(f"SSE 推送 error 事件也失败: {e2}", exc_info=True)
        finally:
            await progress_queue.put(None)

    async def event_generator():
        validate_task = asyncio.ensure_future(run_validate())
        try:
            while True:
                msg = await progress_queue.get()
                if msg is None:
                    break
                yield msg
        except (asyncio.CancelledError, GeneratorExit):
            validate_task.cancel()
        finally:
            if not validate_task.done():
                validate_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/{form_code}/import/sse", summary="SSE 导入表单数据（带进度）")
async def import_form_data_sse(
        form_code: str,
        request: Request,
        file: UploadFile = File(..., description="Excel 文件 (.xlsx)"),
        mode: str = Form(default="append", description="导入模式：append（追加）或 overwrite（覆盖）"),
        data_handling: str = Form(default="insert_only", description="数据处理方式：insert_only / update_only / upsert"),
        match_field: str = Form(default="", description="更新模式下用于匹配已有数据的字段名"),
        db: AsyncSession = Depends(get_db),
):
    """
    通过 SSE 导入表单数据，实时推送导入进度。

    SSE 事件类型：
    - progress: {processed, total, percent, stage, success, fail}
      - stage="parsing" 解析 Excel 阶段
      - stage="importing" 写入数据库阶段
    - completed: {success, fail, errors, message} 导入完成
    - error: {message} 导入失败
    """
    await check_form_permission(form_code, "import", request, db)

    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持 .xlsx 格式")

    if mode not in ("append", "overwrite"):
        raise HTTPException(status_code=400, detail="mode 参数只能是 append 或 overwrite")

    if data_handling not in ("insert_only", "update_only", "upsert"):
        raise HTTPException(status_code=400, detail="data_handling 参数只能是 insert_only、update_only 或 upsert")

    if mode == "append" and data_handling in ("update_only", "upsert") and not match_field:
        raise HTTPException(status_code=400, detail="更新模式下必须指定 match_field")

    content = await file.read()
    service = await FormDataService.create_service(db, form_code)

    progress_queue: asyncio.Queue = asyncio.Queue()

    async def on_progress(processed: int, total: int, stage: str, success: int, fail: int):
        if total > 0:
            if stage == "parsing":
                percent = round(processed / total * 20, 1)
            elif stage == "validating":
                percent = 20 + round(processed / total * 10, 1)
            else:
                percent = 30 + round(processed / total * 69, 1)
        else:
            percent = 0
        await progress_queue.put(
            f"event: progress\ndata: {json.dumps({'processed': processed, 'total': total, 'percent': percent, 'stage': stage, 'success': success, 'fail': fail}, ensure_ascii=False)}\n\n"
        )

    async def run_import():
        try:
            logger.debug(f"SSE import 开始: form_code={form_code}, mode={mode}, data_handling={data_handling}")
            success, fail, errors = await service.import_from_excel(
                db, content, mode=mode, validate_only=False,
                data_handling=data_handling,
                match_field=match_field or None,
                on_progress=on_progress
            )
            completed_data = {
                "success": success,
                "fail": fail,
                "errors": errors,
                "message": f"成功导入 {success} 条，失败 {fail} 条"
            }
            logger.debug(f"SSE import 完成: success={success}, fail={fail}")
            await progress_queue.put(
                f"event: completed\ndata: {json.dumps(completed_data, ensure_ascii=False)}\n\n"
            )
        except Exception as e:
            logger.error(f"SSE 导入失败: {e}", exc_info=True)
            try:
                await progress_queue.put(
                    f"event: error\ndata: {json.dumps({'message': str(e)[:500]}, ensure_ascii=False)}\n\n"
                )
            except Exception as e2:
                logger.error(f"SSE 推送 error 事件也失败: {e2}", exc_info=True)
        finally:
            await progress_queue.put(None)

    async def event_generator():
        import_task = asyncio.ensure_future(run_import())
        try:
            while True:
                msg = await progress_queue.get()
                if msg is None:
                    break
                yield msg
        except (asyncio.CancelledError, GeneratorExit):
            import_task.cancel()
        finally:
            if not import_task.done():
                import_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
