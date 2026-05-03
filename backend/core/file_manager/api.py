#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件管理API
"""
import os
import hashlib
import logging
from typing import Optional, List
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.base_schema import PaginatedResponse, ResponseModel
from core.file_manager.model import FileManager
from core.file_manager.schema import (
    FileManagerResponse,
    FileManagerSimpleResponse,
    CreateFolderIn,
    MoveItemsIn,
    RenameItemIn,
    BatchDeleteIn,
    FileStorageConfigResponse,
    FileStorageConfigUpdate,
    FileUrlResponse,
    CreateAccessTokenIn,
    AccessTokenResponse,
    AccessTokenUrlResponse,
    OcrRecognizeRequest,
    OcrRecognizeResponse,
)
from core.file_manager.service import FileManagerService
from core.file_manager.storage_backends import get_storage_backend
from core.file_manager.temp_token_service import FileAccessTokenService
from core.file_manager.signature_token_service import SignatureTokenService

router = APIRouter(prefix="/file_manager", tags=["文件管理"])

# 配置日志
logger = logging.getLogger(__name__)


def _build_file_response(item: FileManager, has_children: bool = False, parent_name: str = None) -> dict:
    """构建文件响应"""
    return {
        "id": item.id,
        "name": item.name,
        "file_type": item.type,
        "parent_id": item.parent_id,
        "parent_name": parent_name,
        "path": item.path,
        "file_size": item.size,
        "file_ext": item.file_ext,
        "mime_type": item.mime_type,
        "storage_type": item.storage_type,
        "storage_path": item.storage_path,
        "url": item.url,
        "thumbnail_url": item.thumbnail_url,
        "md5": item.md5,
        "is_public": item.is_public,
        "download_count": item.download_count,
        "is_system": item.is_system or False,
        "source": item.source,
        "sys_creator_id": item.sys_creator_id,
        "has_children": has_children,
        "updated_time": item.sys_update_datetime.isoformat() if item.sys_update_datetime else (
            item.sys_create_datetime.isoformat() if item.sys_create_datetime else None
        ),
        "sys_create_datetime": item.sys_create_datetime,
        "sys_update_datetime": item.sys_update_datetime,
    }


# 上传限制配置
MAX_UPLOAD_SIZE = getattr(settings, 'FILE_MAX_UPLOAD_SIZE', 500 * 1024 * 1024)  # 默认500MB
BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.pif', '.vbs', '.js', '.wsh', '.wsf'}


@router.post("/upload", response_model=FileManagerResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    parent_id: Optional[str] = Form(None, alias="parent_id"),
    is_public: bool = Form(False, alias="is_public"),
    source: Optional[str] = Form(None, description="来源模块标识，如 announcement/workflow/chat 等"),
    db: AsyncSession = Depends(get_db),
):
    """上传文件"""
    # 文件扩展名校验
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    if file_ext in BLOCKED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不允许上传此类型文件: {file_ext}")
    
    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)
    
    # 文件大小校验
    if file_size > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {max_mb:.0f}MB）")
    
    # 上传文件
    file_obj = await FileManagerService.upload_file(
        db=db,
        file_content=file_content,
        filename=file.filename,
        file_size=file_size,
        parent_id=parent_id,
        is_public=is_public,
        source=source,
    )
    
    return _build_file_response(file_obj)


@router.post("/folder", response_model=FileManagerResponse, summary="创建文件夹")
async def create_folder(
    data: CreateFolderIn,
    db: AsyncSession = Depends(get_db),
):
    """创建文件夹"""
    folder = await FileManagerService.create_folder(
        db=db,
        name=data.name,
        parent_id=data.parent_id,
    )
    
    if not folder:
        raise HTTPException(status_code=422, detail="同名文件夹已存在")
    
    return _build_file_response(folder)


@router.get("/recent/images", summary="获取最近上传的图片")
async def get_recent_images(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50, description="数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户最近上传的图片文件（跨所有文件夹，按时间倒序）"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        return []
    items = await FileManagerService.get_recent_images(db=db, creator_id=user_id, limit=limit)
    return [_build_file_response(item) for item in items]


@router.get("/recent/files", summary="获取最近上传的文件")
async def get_recent_files(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50, description="数量"),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户最近上传的文件（跨所有文件夹，按时间倒序）"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        return []
    items = await FileManagerService.get_recent_files(db=db, creator_id=user_id, limit=limit)
    return [_build_file_response(item) for item in items]


@router.get("", response_model=PaginatedResponse[FileManagerResponse], summary="获取文件列表")
async def list_files(
    request: Request,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize", description="每页数量"),
    parent_id: Optional[str] = Query(None, description="父文件夹ID"),
    name: Optional[str] = Query(None, description="文件名搜索"),
    type: Optional[str] = Query(None, description="类型: file/folder"),
    storage_type: Optional[str] = Query(None, alias="storageType", description="存储类型"),
    file_ext: Optional[str] = Query(None, alias="fileExt", description="文件扩展名"),
    is_public: Optional[bool] = Query(None, alias="isPublic", description="是否公开"),
    db: AsyncSession = Depends(get_db),
):
    """获取文件列表（分页）"""
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    items, total = await FileManagerService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        parent_id=parent_id,
        name=name,
        type=type,
        storage_type=storage_type,
        file_ext=file_ext,
        is_public=is_public,
        creator_id=user_id,
        is_superuser=is_superuser,
    )
    
    # 批量查询 has_children 和 parent_name，避免 N+1 查询
    folder_ids = [item.id for item in items if item.type == 'folder']
    parent_ids = list({item.parent_id for item in items if item.parent_id})
    
    # 如果是文件夹树请求(type=folder)，只检查是否有子文件夹；否则检查所有子项
    if type == 'folder':
        children_map = await FileManagerService.batch_has_sub_folders(db, folder_ids) if folder_ids else {}
    else:
        children_map = await FileManagerService.batch_has_children(db, folder_ids) if folder_ids else {}
    parent_names_map = await FileManagerService.batch_get_names(db, parent_ids) if parent_ids else {}
    
    # 构建响应
    result_items = []
    for item in items:
        has_children = children_map.get(item.id, False) if item.type == 'folder' else False
        parent_name = parent_names_map.get(item.parent_id) if item.parent_id else None
        result_items.append(_build_file_response(item, has_children, parent_name))
    
    return PaginatedResponse(items=result_items, total=total)


@router.get("/tree", response_model=List[FileManagerResponse], summary="获取文件夹树结构")
async def get_folder_tree(request: Request, db: AsyncSession = Depends(get_db)):
    """获取文件夹树结构"""
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    folders = await FileManagerService.get_folder_tree(db, creator_id=user_id, is_superuser=is_superuser)
    
    # 批量查询 has_children
    folder_ids = [f.id for f in folders]
    children_map = await FileManagerService.batch_has_children(db, folder_ids) if folder_ids else {}
    
    result = []
    for folder in folders:
        has_children = children_map.get(folder.id, False)
        result.append(_build_file_response(folder, has_children))
    
    return result


@router.get("/file_info/{file_id}", response_model=FileManagerSimpleResponse, summary="获取文件信息")
async def get_file_info(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取文件信息"""
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {
        "id": file_obj.id,
        "name": file_obj.name,
        "type": file_obj.type,
        "size": file_obj.size,
        "mime_type": file_obj.mime_type,
        "sys_create_datetime": file_obj.sys_create_datetime.isoformat() if file_obj.sys_create_datetime else None,
    }


@router.put("/{file_id}/rename", response_model=FileManagerResponse, summary="重命名文件/文件夹")
async def rename_item(
    file_id: str,
    data: RenameItemIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """重命名文件/文件夹"""
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    item = await FileManagerService.rename_item(db, file_id, data.name, creator_id=user_id, is_superuser=is_superuser)
    
    if not item:
        raise HTTPException(status_code=400, detail="重命名失败，可能同名文件/文件夹已存在")
    
    return _build_file_response(item)


@router.put("/{file_id}/public", response_model=FileManagerResponse, summary="设置文件公开状态")
async def set_file_public(
    file_id: str,
    request: Request,
    is_public: bool = Query(..., alias="isPublic", description="是否公开"),
    db: AsyncSession = Depends(get_db),
):
    """
    设置文件的公开状态
    
    - 公开文件(is_public=True)：任何人都可以通过URL直接访问，无需认证
    - 私有文件(is_public=False)：需要临时访问令牌才能访问
    """
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 权限校验：普通用户只能修改自己的文件公开状态
    if not is_superuser and user_id and file_obj.sys_creator_id != user_id:
        raise HTTPException(status_code=403, detail="无权修改此文件")
    
    file_obj.is_public = is_public
    await db.commit()
    await db.refresh(file_obj)
    
    return _build_file_response(file_obj)


@router.put("/move", response_model=ResponseModel, summary="移动文件/文件夹")
async def move_items(
    data: MoveItemsIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """移动文件/文件夹"""
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    success = await FileManagerService.move_items(db, data.ids, data.target_folder_id, creator_id=user_id, is_superuser=is_superuser)
    
    if not success:
        raise HTTPException(status_code=400, detail="移动失败")
    
    return ResponseModel(message="移动成功")


@router.delete("/{file_id}", response_model=ResponseModel, summary="删除文件/文件夹")
async def delete_item(
    file_id: str,
    request: Request,
    hard: bool = Query(default=False, description="是否物理删除，默认软删除"),
    db: AsyncSession = Depends(get_db),
):
    """删除文件/文件夹"""
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    success = await FileManagerService.delete_item(db, file_id, hard, creator_id=user_id, is_superuser=is_superuser)
    
    if not success:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return ResponseModel(message="删除成功")


@router.post("/batch/delete", response_model=ResponseModel, summary="批量删除文件/文件夹")
async def batch_delete(
    data: BatchDeleteIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """批量删除文件/文件夹"""
    user_id = getattr(request.state, 'user_id', None)
    is_superuser = getattr(request.state, 'is_superuser', False)
    
    deleted_count = await FileManagerService.batch_delete(db, data.ids, creator_id=user_id, is_superuser=is_superuser)
    return ResponseModel(message=f"成功删除 {deleted_count} 个文件/文件夹")


@router.get("/file/download", summary="下载文件")
async def download_file(
    path: str = Query(..., description="文件存储路径"),
    db: AsyncSession = Depends(get_db),
):
    """下载文件"""
    # 查找文件记录
    file_obj = await FileManagerService.get_by_storage_path(db, path)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 更新下载次数
    await FileManagerService.increment_download_count(db, file_obj.id)
    
    # 获取存储后端
    storage = get_storage_backend()
    
    # 如果是本地存储，直接返回文件
    if file_obj.storage_type == 'local':
        full_path = storage.get_full_path(path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            full_path,
            filename=file_obj.name,
            media_type=file_obj.mime_type or 'application/octet-stream',
        )
    else:
        # 其他存储类型，重定向到实际URL
        if file_obj.url:
            return Response(status_code=302, headers={'Location': file_obj.url})
        else:
            raise HTTPException(status_code=400, detail="无法获取文件URL")


@router.get("/url/{file_id}", response_model=FileUrlResponse, summary="获取文件访问URL")
async def get_file_url(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """通过文件ID获取文件访问URL"""
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj or file_obj.type != 'file':
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # Minio存储，返回临时URL
    if file_obj.storage_type == 'minio':
        storage = get_storage_backend()
        if hasattr(storage, 'get_presigned_url'):
            try:
                temp_url = storage.get_presigned_url(file_obj.storage_path)
                return {"url": temp_url}
            except Exception:
                pass
    
    # 如果文件有直接的URL（云存储）
    if file_obj.url:
        return {"url": file_obj.url}
    
    # 本地存储，构建访问URL
    if file_obj.storage_type == 'local':
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        file_url = f"{base_url}/api/file_manager/file/download?path={file_obj.storage_path}"
        return {"url": file_url}
    
    # 其他情况返回存储路径
    return {"url": file_obj.storage_path}


@router.get("/batch/urls", summary="批量获取文件访问URL")
async def get_batch_file_urls(
    ids: str = Query(..., description="文件ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db),
):
    """批量获取文件访问URL"""
    file_ids = [id_str.strip() for id_str in ids.split(',') if id_str.strip()]
    
    storage = get_storage_backend()
    has_presigned_method = hasattr(storage, 'get_presigned_url')
    
    result = {}
    for file_id in file_ids:
        file_obj = await FileManagerService.get_by_id(db, file_id)
        if not file_obj or file_obj.type != 'file':
            continue
        
        # Minio存储，返回临时URL
        if file_obj.storage_type == 'minio' and has_presigned_method:
            try:
                temp_url = storage.get_presigned_url(file_obj.storage_path)
                result[file_id] = temp_url
                continue
            except Exception:
                pass
        
        if file_obj.url:
            result[file_id] = file_obj.url
        elif file_obj.storage_type == 'local':
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            file_url = f"{base_url}/api/file_manager/file/download?path={file_obj.storage_path}"
            result[file_id] = file_url
        else:
            result[file_id] = file_obj.storage_path
    
    return result


@router.get("/stream/{file_id}", summary="流式传输文件")
async def stream_file(
    request: Request,
    file_id: str,
    token: Optional[str] = Query(None, description="临时访问令牌"),
    db: AsyncSession = Depends(get_db),
):
    """
    通过后端流式传输文件（支持所有存储类型）
    
    访问控制逻辑：
    - 公开文件(is_public=True)：无需任何认证，直接访问
    - 私有文件(is_public=False)：需要提供有效的临时访问令牌
    
    支持 ETag / If-None-Match 缓存协商，命中时返回 304 Not Modified
    """
    # 先获取文件信息，判断是否公开
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj or file_obj.type != 'file':
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 如果文件不是公开的，需要验证临时访问令牌
    if not file_obj.is_public:
        if not token:
            raise HTTPException(status_code=401, detail="需要提供访问令牌")
        token_obj = await FileAccessTokenService.verify_token(db, token)
        if not token_obj:
            raise HTTPException(status_code=401, detail="令牌无效或已过期")
        if token_obj.file_id != file_id:
            raise HTTPException(status_code=403, detail="令牌与文件不匹配")
    
    # ETag 缓存协商：文件内容未变化时直接返回 304
    etag = f'"{file_obj.md5}"' if file_obj.md5 else None
    if etag:
        if_none_match = request.headers.get('if-none-match')
        if if_none_match and if_none_match == etag:
            return Response(status_code=304, headers={'ETag': etag, 'Cache-Control': 'public, max-age=86400'})
    
    # 更新下载次数
    await FileManagerService.increment_download_count(db, file_obj.id)
    
    # 获取存储后端
    storage = get_storage_backend()
    
    # 公共缓存头
    cache_headers = {
        'Cache-Control': 'public, max-age=86400',
    }
    if etag:
        cache_headers['ETag'] = etag
    
    if file_obj.storage_type == 'local':
        # 本地存储直接读取文件
        full_path = storage.get_full_path(file_obj.storage_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        def file_iterator():
            with open(full_path, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk
        
        # 使用 RFC 5987 编码格式支持中文文件名
        encoded_filename = quote(file_obj.name)
        
        return StreamingResponse(
            file_iterator(),
            media_type=file_obj.mime_type or 'application/octet-stream',
            headers={
                'Content-Disposition': f'inline; filename*=UTF-8\'\'{encoded_filename}',
                'Content-Length': str(file_obj.size),
                'Accept-Ranges': 'bytes',
                **cache_headers,
            }
        )
    
    elif file_obj.storage_type == 'minio' and hasattr(storage, 'get_file_content'):
        # Minio存储，通过后端转发
        try:
            file_response = storage.get_file_content(file_obj.storage_path)
            
            # 使用 RFC 5987 编码格式支持中文文件名
            encoded_filename = quote(file_obj.name)
            
            return StreamingResponse(
                file_response,
                media_type=file_obj.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f'inline; filename*=UTF-8\'\'{encoded_filename}',
                    'Content-Length': str(file_obj.size),
                    'Accept-Ranges': 'bytes',
                    **cache_headers,
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")
    
    else:
        # 其他存储类型，重定向到原URL
        if file_obj.url:
            return Response(status_code=302, headers={'Location': file_obj.url})
        else:
            raise HTTPException(status_code=400, detail="不支持的存储类型")


@router.get("/proxy/{file_id}", summary="代理文件访问")
async def proxy_file(
    request: Request,
    file_id: str,
    download: bool = Query(default=False, description="是否作为附件下载"),
    token: Optional[str] = Query(None, description="临时访问令牌"),
    db: AsyncSession = Depends(get_db),
):
    """
    代理文件访问（强制通过后端转发）
    
    访问控制逻辑：
    - 公开文件(is_public=True)：无需任何认证，直接访问
    - 私有文件(is_public=False)：需要提供有效的临时访问令牌
    
    支持 ETag / If-None-Match 缓存协商，命中时返回 304 Not Modified
    """
    # 先获取文件信息，判断是否公开
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj or file_obj.type != 'file':
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 如果文件不是公开的，需要验证临时访问令牌
    if not file_obj.is_public:
        if not token:
            raise HTTPException(status_code=401, detail="需要提供访问令牌")
        token_obj = await FileAccessTokenService.verify_token(db, token)
        if not token_obj:
            raise HTTPException(status_code=401, detail="令牌无效或已过期")
        if token_obj.file_id != file_id:
            raise HTTPException(status_code=403, detail="令牌与文件不匹配")
    
    # ETag 缓存协商：文件内容未变化时直接返回 304
    etag = f'"{file_obj.md5}"' if file_obj.md5 else None
    if etag:
        if_none_match = request.headers.get('if-none-match')
        if if_none_match and if_none_match == etag:
            return Response(status_code=304, headers={'ETag': etag, 'Cache-Control': 'public, max-age=86400'})
    
    # 更新下载次数
    await FileManagerService.increment_download_count(db, file_obj.id)
    
    # 获取存储后端
    storage = get_storage_backend()
    
    disposition = 'attachment' if download else 'inline'
    
    # 公共缓存头
    cache_headers = {
        'Cache-Control': 'public, max-age=86400',
    }
    if etag:
        cache_headers['ETag'] = etag
    
    if file_obj.storage_type == 'local':
        # 本地文件处理
        full_path = storage.get_full_path(file_obj.storage_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        with open(full_path, 'rb') as f:
            content = f.read()
        
        # 使用 RFC 5987 编码格式支持中文文件名
        encoded_filename = quote(file_obj.name)
        
        return Response(
            content=content,
            media_type=file_obj.mime_type or 'application/octet-stream',
            headers={
                'Content-Disposition': f'{disposition}; filename*=UTF-8\'\'{encoded_filename}',
                'Content-Length': str(len(content)),
                **cache_headers,
            }
        )
    
    elif file_obj.storage_type == 'minio' and hasattr(storage, 'get_file_content'):
        # Minio存储处理
        try:
            file_response = storage.get_file_content(file_obj.storage_path)
            content = file_response.read()
            
            # 使用 RFC 5987 编码格式支持中文文件名
            encoded_filename = quote(file_obj.name)
            
            return Response(
                content=content,
                media_type=file_obj.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f'{disposition}; filename*=UTF-8\'\'{encoded_filename}',
                    'Content-Length': str(len(content)),
                    **cache_headers,
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")
    
    else:
        # 其他存储类型重定向
        if file_obj.url:
            return Response(status_code=302, headers={'Location': file_obj.url})
        else:
            raise HTTPException(status_code=400, detail="不支持的存储类型")


@router.get("/storage/config", response_model=FileStorageConfigResponse, summary="获取存储配置")
async def get_storage_config():
    """获取存储配置"""
    config = {
        'storage_type': getattr(settings, 'FILE_STORAGE_TYPE', 'local'),
        'local_base_path': getattr(settings, 'FILE_STORAGE_LOCAL_PATH', None),
    }
    return config


@router.put("/storage/config", response_model=ResponseModel, summary="更新存储配置")
async def update_storage_config(data: FileStorageConfigUpdate):
    """更新存储配置（需要管理员权限）"""
    # TODO: 实现配置更新逻辑，可能需要保存到数据库或配置文件
    return ResponseModel(message="配置更新成功")


@router.post("/access-token", response_model=AccessTokenResponse, summary="创建临时访问令牌")
async def create_access_token(
    data: CreateAccessTokenIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """创建文件临时访问令牌"""
    file_obj = await FileManagerService.get_by_id(db, data.file_id)
    if not file_obj or file_obj.type != 'file':
        raise HTTPException(status_code=404, detail="文件不存在")
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get('user-agent')
    user_id = getattr(request.state, 'user_id', None)
    
    token_obj = await FileAccessTokenService.create_token(
        db=db,
        file_id=data.file_id,
        expires_in_seconds=data.expires_in,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return AccessTokenResponse(
        token=token_obj.token,
        expires_at=token_obj.expires_at,
        file_id=token_obj.file_id,
    )


@router.get("/access-token/url/{file_id}", response_model=AccessTokenUrlResponse, summary="获取带临时令牌的文件URL")
async def get_file_url_with_token(
    file_id: str,
    request: Request,
    expires_in: int = Query(default=3600, alias="expiresIn", description="过期时间（秒）"),
    db: AsyncSession = Depends(get_db),
):
    """获取带临时令牌的文件访问URL"""
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj or file_obj.type != 'file':
        raise HTTPException(status_code=404, detail="文件不存在")
    
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get('user-agent')
    user_id = getattr(request.state, 'user_id', None)
    
    token_obj = await FileAccessTokenService.create_token(
        db=db,
        file_id=file_id,
        expires_in_seconds=expires_in,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    file_url = f"/api/core/file_manager/stream/{file_id}?token={token_obj.token}"
    
    return AccessTokenUrlResponse(
        url=file_url,
        token=token_obj.token,
        expires_at=token_obj.expires_at,
    )


@router.delete("/access-token/{token}", response_model=ResponseModel, summary="撤销临时访问令牌")
async def revoke_access_token(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """撤销临时访问令牌"""
    success = await FileAccessTokenService.revoke_token(db, token)
    if not success:
        raise HTTPException(status_code=404, detail="令牌不存在")
    return ResponseModel(message="令牌已撤销")


@router.post("/access-token/cleanup", response_model=ResponseModel, summary="清理过期令牌")
async def cleanup_expired_tokens(
    db: AsyncSession = Depends(get_db),
):
    """清理过期的临时访问令牌"""
    count = await FileAccessTokenService.cleanup_expired_tokens(db)
    return ResponseModel(message=f"已清理 {count} 个过期令牌")


@router.post("/ocr/recognize", response_model=OcrRecognizeResponse, summary="AI文件智能识别")
async def ocr_recognize(
    request: OcrRecognizeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    使用AI进行文件智能识别，支持多种文件类型。
    
    支持的文件类型：
    - 图片文件：使用 OCR 识别
    - 文本文件：txt, md, log, py, js, json, yaml 等
    - PDF 文件
    - Word 文档：docx, doc
    - Excel 文件：xlsx, xls
    
    参数：
    - **file_id**: 文件ID
    - **output_schema**: 结构化输出字段定义（可选）
    - **prompt**: 自定义提示词（可选）
    """
    # 将 output_schema 转换为字典列表
    output_schema = None
    if request.output_schema:
        output_schema = [field.model_dump() for field in request.output_schema]
    
    result = await FileManagerService.recognize_file_with_function_calling(
        db=db,
        file_id=request.file_id,
        output_schema=output_schema,
        custom_prompt=request.prompt,
    )
    
    return OcrRecognizeResponse(
        success=result["success"],
        raw_text=result.get("raw_text"),
        extracted_data=result.get("extracted_data"),
        error=result.get("error"),
    )


@router.get("/{file_id}", response_model=FileManagerResponse, summary="获取文件详情")
async def get_file_detail(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取文件详情"""
    file_obj = await FileManagerService.get_by_id(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    has_children = False
    if file_obj.type == 'folder':
        has_children = await FileManagerService.has_children(db, file_obj.id)
    
    parent_name = None
    if file_obj.parent_id:
        parent = await FileManagerService.get_by_id(db, file_obj.parent_id)
        if parent:
            parent_name = parent.name
    
    return _build_file_response(file_obj, has_children, parent_name)


# ==================== 签名令牌相关 API ====================

@router.post("/signature/token", summary="创建签名令牌")
async def create_signature_token(
    source: str = Form(default="form", description="来源"),
    expire_minutes: int = Form(default=30, description="过期时间(分钟)"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    创建签名令牌，用于手机扫码签名
    
    返回:
    - token: 签名令牌（用于构建二维码URL）
    - callback_key: 回调标识（用于前端轮询签名状态）
    - expired_at: 过期时间
    """
    user_id = getattr(request.state, 'user_id', None) if request else None
    
    sign_token = await SignatureTokenService.create_token(
        db=db,
        source=source,
        expire_minutes=expire_minutes,
        user_id=user_id,
    )
    
    return {
        "token": sign_token.token,
        "callback_key": sign_token.callback_key,
        "expired_at": sign_token.expired_at.isoformat(),
    }


@router.get("/signature/status/{callback_key}", summary="检查签名状态")
async def check_signature_status(
    callback_key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    检查签名状态（用于前端轮询）
    
    返回:
    - status: pending/completed/expired/not_found
    - message: 状态描述
    - file_id: 签名文件ID（仅当status=completed时）
    """
    return await SignatureTokenService.check_signature_status(db, callback_key)


@router.get("/signature/info/{token}", summary="获取签名令牌信息（无需登录）")
async def get_signature_token_info(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    根据令牌获取签名信息（移动端使用，无需登录）
    """
    sign_token = await SignatureTokenService.get_by_token(db, token)
    if not sign_token:
        raise HTTPException(status_code=404, detail="签名链接无效")
    
    is_valid, error_msg = SignatureTokenService.validate_token(sign_token)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    return {
        "token": sign_token.token,
        "source": sign_token.source,
        "expired_at": sign_token.expired_at.isoformat(),
    }


@router.post("/signature/upload/{token}", summary="上传签名图片（无需登录）")
async def upload_signature_image(
    token: str,
    file: UploadFile = File(..., description="签名图片文件"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    上传签名图片并完成签名（移动端使用，无需登录）
    
    参数:
    - token: 签名令牌
    - file: 签名图片文件（仅支持 PNG/JPEG）
    """
    # 验证令牌
    sign_token = await SignatureTokenService.get_by_token(db, token)
    if not sign_token:
        raise HTTPException(status_code=404, detail="签名链接无效")
    
    is_valid, error_msg = SignatureTokenService.validate_token(sign_token)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 PNG 或 JPEG 格式")
    
    # 验证文件大小（最大 5MB）
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    
    try:
        # 上传文件
        uploaded_file = await FileManagerService.upload_file(
            db=db,
            file_content=content,
            filename=file.filename or f"signature_{datetime.now().strftime('%Y%m%d%H%M%S')}.png",
            file_size=len(content),
            source='form',  # 归类到表单附件
            parent_id=None,
            is_public=False,
        )
        
        # 获取客户端信息
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
            user_agent = request.headers.get("User-Agent")
        
        # 完成签名
        sign_token = await SignatureTokenService.complete_signature(
            db=db,
            sign_token=sign_token,
            signature_file_id=uploaded_file.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return {
            "success": True,
            "message": "签名完成",
            "file_id": sign_token.signature_file_id,
        }
    except Exception as e:
        logger.exception("上传签名图片失败")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/signature/complete/{token}", summary="完成签名（无需登录）")
async def complete_signature(
    token: str,
    signature_file_id: str = Form(..., description="签名文件ID"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    完成签名（移动端使用，无需登录）
    
    参数:
    - token: 签名令牌
    - signature_file_id: 已上传的签名图片文件ID
    """
    sign_token = await SignatureTokenService.get_by_token(db, token)
    if not sign_token:
        raise HTTPException(status_code=404, detail="签名链接无效")
    
    is_valid, error_msg = SignatureTokenService.validate_token(sign_token)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 获取客户端信息
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
        user_agent = request.headers.get("User-Agent")
    
    sign_token = await SignatureTokenService.complete_signature(
        db=db,
        sign_token=sign_token,
        signature_file_id=signature_file_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return {
        "success": True,
        "message": "签名完成",
        "file_id": sign_token.signature_file_id,
    }
