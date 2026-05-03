#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis管理API（异步版本）
"""
import logging

from fastapi import APIRouter, HTTPException

from core.redis_manager.schema import (
    RedisKeyDetailSchema,
    RedisKeyCreateSchema,
    RedisKeyUpdateSchema,
    RedisKeySearchSchema,
    RedisKeyListResponse,
    RedisDatabaseListResponse,
    RedisKeyRenameSchema,
    RedisKeyExpireSchema,
    RedisBatchDeleteSchema,
    RedisFlushDBSchema,
    RedisOperationResponse
)
from core.redis_manager.service import AsyncRedisManagerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/redis_manager", tags=["Redis管理"])


@router.get("/databases", response_model=RedisDatabaseListResponse, summary="获取所有Redis数据库信息")
async def get_redis_databases():
    """获取所有Redis数据库信息"""
    try:
        service = AsyncRedisManagerService(db_index=0)
        databases, total_keys = await service.get_all_databases()
        await service.close()

        return {
            'databases': databases,
            'total_keys': total_keys
        }
    except Exception as e:
        logger.error(f"Failed to get redis databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{db_index}/keys/search", response_model=RedisKeyListResponse, summary="搜索Redis键")
async def search_redis_keys(db_index: int, search: RedisKeySearchSchema):
    """搜索Redis键"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        keys, total = await service.search_keys(
            pattern=search.pattern,
            key_type=search.key_type,
            page=search.page,
            page_size=search.page_size
        )
        await service.close()

        return {
            'total': total,
            'keys': keys,
            'page': search.page,
            'page_size': search.page_size
        }
    except Exception as e:
        logger.error(f"Failed to search redis keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{db_index}/keys/{key:path}", response_model=RedisKeyDetailSchema, summary="获取Redis键详情")
async def get_redis_key_detail(db_index: int, key: str):
    """获取Redis键详情"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        detail = await service.get_key_detail(key)
        await service.close()

        return detail
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get redis key detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{db_index}/keys", response_model=RedisOperationResponse, summary="创建Redis键")
async def create_redis_key(db_index: int, data: RedisKeyCreateSchema):
    """创建Redis键"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        success = await service.create_key(
            key=data.key,
            key_type=data.type,
            value=data.value,
            ttl=data.ttl
        )
        await service.close()

        return {
            'success': success,
            'message': f"Key '{data.key}' created successfully"
        }
    except ValueError as e:
        return {
            'success': False,
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Failed to create redis key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{db_index}/keys/{key:path}", response_model=RedisOperationResponse, summary="更新Redis键")
async def update_redis_key(db_index: int, key: str, data: RedisKeyUpdateSchema):
    """更新Redis键"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        success = await service.update_key(
            key=key,
            value=data.value,
            ttl=data.ttl
        )
        await service.close()

        return {
            'success': success,
            'message': f"Key '{key}' updated successfully"
        }
    except ValueError as e:
        return {
            'success': False,
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Failed to update redis key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{db_index}/keys/{key:path}", response_model=RedisOperationResponse, summary="删除Redis键")
async def delete_redis_key(db_index: int, key: str):
    """删除Redis键"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        success = await service.delete_key(key)
        await service.close()

        return {
            'success': success,
            'message': f"Key '{key}' deleted successfully" if success else f"Key '{key}' not found"
        }
    except Exception as e:
        logger.error(f"Failed to delete redis key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{db_index}/keys/batch-delete", response_model=RedisOperationResponse, summary="批量删除Redis键")
async def batch_delete_redis_keys(db_index: int, data: RedisBatchDeleteSchema):
    """批量删除Redis键"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        count = await service.batch_delete_keys(data.keys)
        await service.close()

        return {
            'success': True,
            'message': f"Deleted {count} keys",
            'data': {'deleted_count': count}
        }
    except Exception as e:
        logger.error(f"Failed to batch delete redis keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{db_index}/keys/rename", response_model=RedisOperationResponse, summary="重命名Redis键")
async def rename_redis_key(db_index: int, data: RedisKeyRenameSchema):
    """重命名Redis键"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        success = await service.rename_key(data.old_key, data.new_key)
        await service.close()

        return {
            'success': success,
            'message': f"Key renamed from '{data.old_key}' to '{data.new_key}'"
        }
    except ValueError as e:
        return {
            'success': False,
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Failed to rename redis key: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{db_index}/keys/expire", response_model=RedisOperationResponse, summary="设置Redis键过期时间")
async def set_redis_key_expire(db_index: int, data: RedisKeyExpireSchema):
    """设置Redis键过期时间"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        success = await service.set_expire(data.key, data.ttl)
        await service.close()

        ttl_msg = "永不过期" if data.ttl == -1 else f"{data.ttl}秒后过期"
        return {
            'success': success,
            'message': f"Key '{data.key}' set to {ttl_msg}"
        }
    except ValueError as e:
        return {
            'success': False,
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Failed to set redis key expire: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{db_index}/flush", response_model=RedisOperationResponse, summary="清空Redis数据库")
async def flush_redis_database(db_index: int, data: RedisFlushDBSchema):
    """清空Redis数据库"""
    try:
        service = AsyncRedisManagerService(db_index=db_index)
        success = await service.flush_db(confirm=data.confirm)
        await service.close()

        return {
            'success': success,
            'message': f"Database {db_index} flushed successfully"
        }
    except ValueError as e:
        return {
            'success': False,
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Failed to flush redis database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
