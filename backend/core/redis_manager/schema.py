#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis管理Schema
"""
from datetime import datetime
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, Field

from app.base_schema import CSTDatetime


class RedisKeySchema(BaseModel):
    """Redis键Schema"""
    key: str
    type: str  # string, list, set, zset, hash
    ttl: int  # -1表示永不过期，-2表示已过期
    size: Optional[int] = None  # 键的大小（字节）
    length: Optional[int] = None  # 集合/列表的元素数量
    encoding: Optional[str] = None  # 编码方式


class RedisKeyDetailSchema(BaseModel):
    """Redis键详情Schema"""
    key: str
    type: str
    ttl: int
    value: Any  # 根据类型不同，值的格式也不同
    size: Optional[int] = None
    encoding: Optional[str] = None
    created_at: Optional[CSTDatetime] = None


class RedisKeyCreateSchema(BaseModel):
    """创建Redis键Schema"""
    key: str = Field(..., description="键名")
    type: str = Field(..., description="数据类型: string, list, set, zset, hash")
    value: Any = Field(..., description="值")
    ttl: Optional[int] = Field(None, description="过期时间（秒），-1表示永不过期")


class RedisKeyUpdateSchema(BaseModel):
    """更新Redis键Schema"""
    value: Any = Field(..., description="新值")
    ttl: Optional[int] = Field(None, description="过期时间（秒）")


class RedisStringValueSchema(BaseModel):
    """String类型值Schema"""
    value: str


class RedisListValueSchema(BaseModel):
    """List类型值Schema"""
    values: List[str]


class RedisSetValueSchema(BaseModel):
    """Set类型值Schema"""
    members: List[str]


class RedisZSetValueSchema(BaseModel):
    """ZSet类型值Schema"""
    members: List[Dict[str, Any]]  # [{"member": "xxx", "score": 1.0}]


class RedisHashValueSchema(BaseModel):
    """Hash类型值Schema"""
    fields: Dict[str, str]


class RedisKeySearchSchema(BaseModel):
    """Redis键搜索Schema"""
    pattern: str = Field(default="*", description="搜索模式，支持通配符")
    key_type: Optional[str] = Field(None, description="键类型过滤")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class RedisKeyListResponse(BaseModel):
    """Redis键列表响应Schema"""
    total: int
    keys: List[RedisKeySchema]
    page: int
    page_size: int


class RedisDatabaseSchema(BaseModel):
    """Redis数据库Schema"""
    db_index: int
    keys_count: int
    expires_count: int
    avg_ttl: int


class RedisDatabaseListResponse(BaseModel):
    """Redis数据库列表响应Schema"""
    databases: List[RedisDatabaseSchema]
    total_keys: int


class RedisKeyRenameSchema(BaseModel):
    """重命名键Schema"""
    old_key: str
    new_key: str


class RedisKeyExpireSchema(BaseModel):
    """设置过期时间Schema"""
    key: str
    ttl: int  # 秒


class RedisBatchDeleteSchema(BaseModel):
    """批量删除Schema"""
    keys: List[str]


class RedisFlushDBSchema(BaseModel):
    """清空数据库Schema"""
    db_index: int
    confirm: bool = Field(..., description="确认清空")


class RedisOperationResponse(BaseModel):
    """操作响应Schema"""
    success: bool
    message: str
    data: Optional[Any] = None
