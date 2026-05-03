#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分块上传API
"""
import hashlib
import mimetypes
import os
import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from utils.redis import RedisClient
from app.base_schema import ResponseModel
from core.file_manager.model import FileManager
from core.file_manager.schema import (
    InitChunkUploadIn,
    InitChunkUploadOut,
    UploadChunkOut,
    MergeChunksIn,
    ChunkUploadStatusOut,
    FileManagerResponse,
)
from core.file_manager.service import FileManagerService
from core.file_manager.storage_backends import get_storage_backend

router = APIRouter(prefix="/file_manager/chunk", tags=["分块上传"])

# 分块上传临时目录
CHUNK_UPLOAD_DIR = os.path.join('media', 'chunk_uploads')
os.makedirs(CHUNK_UPLOAD_DIR, exist_ok=True)

# 缓存过期时间（7天）
CACHE_EXPIRE_SECONDS = 7 * 24 * 3600


def get_chunk_upload_key(upload_id: str) -> str:
    """获取分块上传的缓存键"""
    return f'chunk_upload:{upload_id}'


def get_chunk_set_key(upload_id: str) -> str:
    """获取分块上传的已上传分块集合键（使用Redis Set保证原子性）"""
    return f'chunk_upload_set:{upload_id}'


def get_chunk_dir(upload_id: str) -> str:
    """获取分块存储目录"""
    chunk_dir = os.path.join(CHUNK_UPLOAD_DIR, upload_id)
    os.makedirs(chunk_dir, exist_ok=True)
    return chunk_dir


def get_chunk_path(upload_id: str, chunk_index: int) -> str:
    """获取分块文件路径"""
    return os.path.join(get_chunk_dir(upload_id), f'chunk_{chunk_index}')


def _build_file_response(item: FileManager) -> dict:
    """构建文件响应"""
    return {
        "id": item.id,
        "name": item.name,
        "file_type": item.type,
        "parent_id": item.parent_id,
        "parent_name": None,
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
        "has_children": False,
        "updated_time": item.sys_update_datetime.isoformat() if item.sys_update_datetime else (
            item.sys_create_datetime.isoformat() if item.sys_create_datetime else None
        ),
        "sys_create_datetime": item.sys_create_datetime,
        "sys_update_datetime": item.sys_update_datetime,
    }


@router.post("/init", response_model=InitChunkUploadOut, summary="初始化分块上传")
async def init_chunk_upload(
    data: InitChunkUploadIn,
    db: AsyncSession = Depends(get_db),
):
    """
    初始化分块上传
    
    - 检查文件是否已存在（秒传功能）
    - 生成上传ID
    - 计算分块数量
    - 返回上传配置信息
    """
    # 检查文件是否已存在（秒传）
    if data.file_hash:
        existing_file = await FileManagerService.get_by_md5(db, data.file_hash, data.total_size)
        
        if existing_file:
            # 文件已存在，秒传
            return {
                'upload_id': str(uuid.uuid4()),
                'chunk_size': data.chunk_size,
                'total_chunks': 0,
                'uploaded_chunks': [],
                'file_exists': True,
                'file_id': existing_file.id,
            }
    
    # 生成上传ID
    upload_id = str(uuid.uuid4())
    
    # 计算总分块数
    total_chunks = (data.total_size + data.chunk_size - 1) // data.chunk_size
    
    # 在缓存中保存上传信息
    upload_info = {
        'upload_id': upload_id,
        'filename': data.filename,
        'total_size': data.total_size,
        'chunk_size': data.chunk_size,
        'total_chunks': total_chunks,
        'uploaded_chunks': [],
        'parent_id': data.parent_id,
        'is_public': data.is_public,
        'created_at': datetime.now().isoformat(),
    }
    
    cache_key = get_chunk_upload_key(upload_id)
    await RedisClient.set(cache_key, upload_info, expire=CACHE_EXPIRE_SECONDS)
    
    # 初始化已上传分块集合（使用Redis Set保证并发安全）
    set_key = get_chunk_set_key(upload_id)
    client = await RedisClient.get_client()
    await client.delete(set_key)
    await client.expire(set_key, CACHE_EXPIRE_SECONDS)
    
    return {
        'upload_id': upload_id,
        'chunk_size': data.chunk_size,
        'total_chunks': total_chunks,
        'uploaded_chunks': [],
        'file_exists': False,
        'file_id': None,
    }


@router.post("/upload", response_model=UploadChunkOut, summary="上传分块")
async def upload_chunk(
    upload_id: str = Form(..., alias="uploadId"),
    chunk_index: int = Form(..., alias="chunkIndex"),
    chunk: UploadFile = File(...),
):
    """
    上传单个分块
    
    - 接收分块数据
    - 保存到临时目录
    - 更新上传进度
    """
    # 获取上传信息
    cache_key = get_chunk_upload_key(upload_id)
    upload_info = await RedisClient.get(cache_key)
    
    if not upload_info:
        raise HTTPException(status_code=404, detail="上传会话不存在或已过期")
    
    # 验证分块索引
    if chunk_index < 0 or chunk_index >= upload_info['total_chunks']:
        raise HTTPException(status_code=400, detail=f"无效的分块索引: {chunk_index}")
    
    # 保存分块文件
    chunk_path = get_chunk_path(upload_id, chunk_index)
    
    try:
        chunk_content = await chunk.read()
        with open(chunk_path, 'wb') as f:
            f.write(chunk_content)
        
        # 使用 Redis SADD 原子操作更新已上传分块集合，保证并发安全
        set_key = get_chunk_set_key(upload_id)
        client = await RedisClient.get_client()
        await client.sadd(set_key, str(chunk_index))
        await client.expire(set_key, CACHE_EXPIRE_SECONDS)
        
        return {
            'chunk_index': chunk_index,
            'uploaded': True,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分块上传失败: {str(e)}")


@router.get("/status", response_model=ChunkUploadStatusOut, summary="获取分块上传状态")
async def get_chunk_upload_status(
    upload_id: str = Query(..., alias="uploadId"),
):
    """
    获取分块上传状态
    
    - 查询已上传的分块
    - 返回上传进度
    """
    cache_key = get_chunk_upload_key(upload_id)
    upload_info = await RedisClient.get(cache_key)
    
    if not upload_info:
        raise HTTPException(status_code=404, detail="上传会话不存在或已过期")
    
    # 从 Redis Set 获取已上传分块列表
    set_key = get_chunk_set_key(upload_id)
    client = await RedisClient.get_client()
    uploaded_set = await client.smembers(set_key)
    uploaded_chunks = sorted([int(x) for x in uploaded_set])
    
    completed = len(uploaded_chunks) == upload_info['total_chunks']
    
    return {
        'upload_id': upload_id,
        'filename': upload_info['filename'],
        'total_size': upload_info['total_size'],
        'total_chunks': upload_info['total_chunks'],
        'uploaded_chunks': uploaded_chunks,
        'completed': completed,
    }


@router.post("/merge", response_model=FileManagerResponse, summary="合并分块")
async def merge_chunks(
    data: MergeChunksIn,
    db: AsyncSession = Depends(get_db),
):
    """
    合并分块文件
    
    - 验证所有分块已上传
    - 按顺序合并分块
    - 计算文件MD5
    - 保存到存储后端
    - 创建数据库记录
    - 清理临时文件
    """
    upload_id = data.upload_id
    cache_key = get_chunk_upload_key(upload_id)
    upload_info = await RedisClient.get(cache_key)
    
    if not upload_info:
        raise HTTPException(status_code=404, detail="上传会话不存在或已过期")
    
    # 从 Redis Set 获取已上传分块列表
    set_key = get_chunk_set_key(upload_id)
    client = await RedisClient.get_client()
    uploaded_set = await client.smembers(set_key)
    uploaded_chunks = [int(x) for x in uploaded_set]
    
    # 验证所有分块已上传
    if len(uploaded_chunks) != upload_info['total_chunks']:
        missing_chunks = [
            i for i in range(upload_info['total_chunks'])
            if i not in uploaded_chunks
        ]
        raise HTTPException(status_code=400, detail=f"分块上传未完成，缺少分块: {missing_chunks}")
    
    try:
        # 获取父文件夹路径
        folder_path = ''
        if upload_info['parent_id']:
            parent = await FileManagerService.get_by_id(db, upload_info['parent_id'])
            if parent and parent.type == 'folder':
                folder_path = parent.path
        
        # 创建临时合并文件
        temp_merged_path = os.path.join(get_chunk_dir(upload_id), 'merged_file')
        md5_hash = hashlib.md5()
        
        # 按顺序合并分块
        with open(temp_merged_path, 'wb') as merged_file:
            for chunk_index in range(upload_info['total_chunks']):
                chunk_path = get_chunk_path(upload_id, chunk_index)
                
                if not os.path.exists(chunk_path):
                    raise HTTPException(status_code=500, detail=f"分块 {chunk_index} 不存在")
                
                with open(chunk_path, 'rb') as chunk_file:
                    chunk_data = chunk_file.read()
                    merged_file.write(chunk_data)
                    md5_hash.update(chunk_data)
        
        # 计算MD5
        file_md5 = md5_hash.hexdigest()
        
        # 检查是否已存在相同文件（合并后的秒传检查）
        existing_file = await FileManagerService.get_by_md5(db, file_md5, upload_info['total_size'])
        
        if existing_file:
            # 清理临时文件和缓存
            shutil.rmtree(get_chunk_dir(upload_id), ignore_errors=True)
            await RedisClient.delete(cache_key)
            await client.delete(set_key)
            
            # 返回已存在的文件
            return _build_file_response(existing_file)
        
        # 获取存储后端
        storage = get_storage_backend()
        
        # 计算文件信息
        filename = upload_info['filename']
        file_ext = os.path.splitext(filename)[1].lower()
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        # 保存到存储后端
        with open(temp_merged_path, 'rb') as merged_file:
            storage_path, url = storage.save(merged_file, filename, folder_path)
        
        # 构建完整路径
        full_path = os.path.join(folder_path, filename).replace('\\', '/') if folder_path else filename
        
        # 创建数据库记录
        file_obj = FileManager(
            name=filename,
            type='file',
            parent_id=upload_info['parent_id'],
            path=full_path,
            size=upload_info['total_size'],
            file_ext=file_ext,
            mime_type=mime_type,
            storage_type=storage.__class__.__name__.replace('StorageBackend', '').lower(),
            storage_path=storage_path,
            url=url,
            md5=file_md5,
            is_public=upload_info['is_public'],
        )
        db.add(file_obj)
        await db.commit()
        await db.refresh(file_obj)
        
        # 清理临时文件和缓存
        shutil.rmtree(get_chunk_dir(upload_id), ignore_errors=True)
        await RedisClient.delete(cache_key)
        await client.delete(set_key)
        
        return _build_file_response(file_obj)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合并文件失败: {str(e)}")


@router.delete("/cancel", response_model=ResponseModel, summary="取消分块上传")
async def cancel_chunk_upload(
    upload_id: str = Query(..., alias="uploadId"),
):
    """
    取消分块上传
    
    - 清理临时文件
    - 删除缓存信息
    """
    try:
        # 清理临时文件
        shutil.rmtree(get_chunk_dir(upload_id), ignore_errors=True)
        
        # 删除缓存和Set
        cache_key = get_chunk_upload_key(upload_id)
        await RedisClient.delete(cache_key)
        set_key = get_chunk_set_key(upload_id)
        client = await RedisClient.get_client()
        await client.delete(set_key)
        
        return ResponseModel(message="上传已取消")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消上传失败: {str(e)}")
