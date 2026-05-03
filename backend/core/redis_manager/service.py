#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis管理服务（异步版本）
"""
import logging
from typing import List, Dict, Any, Optional, Tuple

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class AsyncRedisManagerService:
    """异步Redis管理服务"""

    def __init__(self, db_index: int = 0):
        """
        初始化Redis连接
        
        Args:
            db_index: Redis数据库索引（0-15）
        """
        redis_host = settings.REDIS_HOST
        redis_port = settings.REDIS_PORT
        redis_password = settings.REDIS_PASSWORD
        if redis_password == '':
            redis_password = None

        # 不自动解码，因为可能有二进制数据
        self.client = aioredis.Redis(
            host=redis_host,
            port=redis_port,
            db=db_index,
            password=redis_password,
            decode_responses=False  # 不自动解码，手动处理
        )
        self.db_index = db_index
        self.host = redis_host
        self.port = redis_port
        self.password = redis_password

    def _safe_decode(self, value: any) -> str:
        """安全解码Redis值"""
        if value is None:
            return ''
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                import base64
                return f"<binary data: {base64.b64encode(value).decode('ascii')}>"
        return str(value)

    async def get_all_databases(self) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取所有Redis数据库信息
        
        Returns:
            (数据库列表, 总键数)
        """
        databases = []
        total_keys = 0

        # Redis默认有16个数据库（0-15）
        for db_idx in range(16):
            try:
                temp_client = aioredis.Redis(
                    host=self.host,
                    port=self.port,
                    db=db_idx,
                    password=self.password,
                    decode_responses=True
                )

                # 获取数据库信息
                info = await temp_client.info('keyspace')
                db_key = f'db{db_idx}'

                if db_key in info:
                    db_info = info[db_key]
                    keys_count = db_info.get('keys', 0)
                    expires_count = db_info.get('expires', 0)
                    avg_ttl = db_info.get('avg_ttl', 0)
                else:
                    keys_count = 0
                    expires_count = 0
                    avg_ttl = 0

                databases.append({
                    'db_index': db_idx,
                    'keys_count': keys_count,
                    'expires_count': expires_count,
                    'avg_ttl': avg_ttl
                })

                total_keys += keys_count
                await temp_client.aclose()

            except Exception as e:
                logger.error(f"Failed to get info for db{db_idx}: {e}")
                databases.append({
                    'db_index': db_idx,
                    'keys_count': 0,
                    'expires_count': 0,
                    'avg_ttl': 0
                })

        return databases, total_keys

    async def search_keys(
            self,
            pattern: str = "*",
            key_type: Optional[str] = None,
            page: int = 1,
            page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        搜索Redis键
        
        Args:
            pattern: 搜索模式
            key_type: 键类型过滤
            page: 页码
            page_size: 每页数量
            
        Returns:
            (键列表, 总数)
        """
        try:
            # 使用SCAN命令遍历所有键
            all_keys = []
            cursor = 0

            while True:
                cursor, keys = await self.client.scan(
                    cursor,
                    match=pattern.encode() if isinstance(pattern, str) else pattern,
                    count=100
                )
                all_keys.extend([self._safe_decode(k) for k in keys])
                if cursor == 0:
                    break

            logger.info(f"Scanned {len(all_keys)} keys with pattern '{pattern}'")

            # 按类型过滤
            if key_type:
                filtered_keys = []
                for key in all_keys:
                    ktype = await self.client.type(key)
                    ktype_str = self._safe_decode(ktype)
                    if ktype_str == key_type:
                        filtered_keys.append(key)
                logger.info(f"Filtered to {len(filtered_keys)} keys of type '{key_type}'")
                all_keys = filtered_keys

            total = len(all_keys)
            logger.info(f"Total keys: {total}, returning page {page} with {page_size} items per page")

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            page_keys = all_keys[start:end]

            # 获取键的详细信息
            keys_info = []
            for key in page_keys:
                try:
                    key_info = await self._get_key_info(key)
                    keys_info.append(key_info)
                except Exception as e:
                    logger.error(f"Failed to get info for key {key}: {e}")
                    keys_info.append({
                        'key': key,
                        'type': 'unknown',
                        'ttl': -1,
                        'size': None,
                        'length': None,
                        'encoding': None
                    })

            return keys_info, total

        except Exception as e:
            logger.error(f"Failed to search keys: {e}")
            raise

    async def _get_key_info(self, key: str) -> Dict[str, Any]:
        """获取键的基本信息"""
        key_bytes = key.encode() if isinstance(key, str) else key
        key_type = self._safe_decode(await self.client.type(key_bytes))
        ttl = await self.client.ttl(key_bytes)

        info = {
            'key': key,
            'type': key_type,
            'ttl': ttl,
            'encoding': None
        }

        # 获取编码信息
        try:
            if await self.client.exists(key_bytes):
                encoding = await self.client.object('encoding', key_bytes)
                info['encoding'] = self._safe_decode(encoding) if encoding else None
        except Exception:
            pass

        # 获取大小和长度
        if key_type == 'string':
            value = await self.client.get(key_bytes)
            info['size'] = len(value) if value else 0
        elif key_type == 'list':
            info['length'] = await self.client.llen(key_bytes)
        elif key_type == 'set':
            info['length'] = await self.client.scard(key_bytes)
        elif key_type == 'zset':
            info['length'] = await self.client.zcard(key_bytes)
        elif key_type == 'hash':
            info['length'] = await self.client.hlen(key_bytes)

        return info

    async def get_key_detail(self, key: str) -> Dict[str, Any]:
        """
        获取键的详细信息
        
        Args:
            key: 键名
            
        Returns:
            键的详细信息
        """
        key_bytes = key.encode() if isinstance(key, str) else key

        if not await self.client.exists(key_bytes):
            raise ValueError(f"Key '{key}' does not exist")

        key_type = self._safe_decode(await self.client.type(key_bytes))
        ttl = await self.client.ttl(key_bytes)

        detail = {
            'key': key,
            'type': key_type,
            'ttl': ttl,
            'encoding': None
        }

        # 获取编码信息
        try:
            encoding = await self.client.object('encoding', key_bytes)
            detail['encoding'] = self._safe_decode(encoding) if encoding else None
        except Exception:
            pass

        # 根据类型获取值
        if key_type == 'string':
            value = await self.client.get(key_bytes)
            detail['value'] = self._safe_decode(value)
            detail['size'] = len(value) if value else 0
        elif key_type == 'list':
            values = await self.client.lrange(key_bytes, 0, -1)
            detail['value'] = [self._safe_decode(v) for v in values]
            detail['length'] = len(values)
        elif key_type == 'set':
            members = await self.client.smembers(key_bytes)
            detail['value'] = [self._safe_decode(m) for m in members]
            detail['length'] = len(members)
        elif key_type == 'zset':
            members = await self.client.zrange(key_bytes, 0, -1, withscores=True)
            detail['value'] = [{'member': self._safe_decode(m), 'score': s} for m, s in members]
            detail['length'] = len(members)
        elif key_type == 'hash':
            hash_data = await self.client.hgetall(key_bytes)
            detail['value'] = {self._safe_decode(k): self._safe_decode(v) for k, v in hash_data.items()}
            detail['length'] = len(hash_data)

        return detail

    async def create_key(self, key: str, key_type: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        创建Redis键
        
        Args:
            key: 键名
            key_type: 数据类型
            value: 值
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
        """
        try:
            # 检查键是否已存在
            if await self.client.exists(key):
                raise ValueError(f"Key '{key}' already exists")

            # 根据类型设置值
            if key_type == 'string':
                await self.client.set(key, value)
            elif key_type == 'list':
                if isinstance(value, list):
                    await self.client.rpush(key, *value)
                else:
                    raise ValueError("List type requires a list value")
            elif key_type == 'set':
                if isinstance(value, list):
                    await self.client.sadd(key, *value)
                else:
                    raise ValueError("Set type requires a list value")
            elif key_type == 'zset':
                if isinstance(value, list):
                    mapping = {item['member']: item['score'] for item in value}
                    await self.client.zadd(key, mapping)
                else:
                    raise ValueError("ZSet type requires a list of {member, score} dicts")
            elif key_type == 'hash':
                if isinstance(value, dict):
                    await self.client.hset(key, mapping=value)
                else:
                    raise ValueError("Hash type requires a dict value")
            else:
                raise ValueError(f"Unsupported type: {key_type}")

            # 设置过期时间
            if ttl and ttl > 0:
                await self.client.expire(key, ttl)

            return True

        except Exception as e:
            logger.error(f"Failed to create key {key}: {e}")
            raise

    async def update_key(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        更新Redis键
        
        Args:
            key: 键名
            value: 新值
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
        """
        try:
            if not await self.client.exists(key):
                raise ValueError(f"Key '{key}' does not exist")

            key_type = self._safe_decode(await self.client.type(key))

            # 删除旧值
            await self.client.delete(key)

            # 设置新值
            if key_type == 'string':
                await self.client.set(key, value)
            elif key_type == 'list':
                if isinstance(value, list):
                    await self.client.rpush(key, *value)
                else:
                    raise ValueError("List type requires a list value")
            elif key_type == 'set':
                if isinstance(value, list):
                    await self.client.sadd(key, *value)
                else:
                    raise ValueError("Set type requires a list value")
            elif key_type == 'zset':
                if isinstance(value, list):
                    mapping = {item['member']: item['score'] for item in value}
                    await self.client.zadd(key, mapping)
                else:
                    raise ValueError("ZSet type requires a list of {member, score} dicts")
            elif key_type == 'hash':
                if isinstance(value, dict):
                    await self.client.hset(key, mapping=value)
                else:
                    raise ValueError("Hash type requires a dict value")

            # 设置过期时间
            if ttl is not None:
                if ttl > 0:
                    await self.client.expire(key, ttl)
                elif ttl == -1:
                    await self.client.persist(key)

            return True

        except Exception as e:
            logger.error(f"Failed to update key {key}: {e}")
            raise

    async def delete_key(self, key: str) -> bool:
        """
        删除Redis键
        
        Args:
            key: 键名
            
        Returns:
            是否成功
        """
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            raise

    async def batch_delete_keys(self, keys: List[str]) -> int:
        """
        批量删除Redis键
        
        Args:
            keys: 键名列表
            
        Returns:
            删除的键数量
        """
        try:
            if not keys:
                return 0
            return await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to batch delete keys: {e}")
            raise

    async def rename_key(self, old_key: str, new_key: str) -> bool:
        """
        重命名键
        
        Args:
            old_key: 旧键名
            new_key: 新键名
            
        Returns:
            是否成功
        """
        try:
            if not await self.client.exists(old_key):
                raise ValueError(f"Key '{old_key}' does not exist")

            if await self.client.exists(new_key):
                raise ValueError(f"Key '{new_key}' already exists")

            await self.client.rename(old_key, new_key)
            return True

        except Exception as e:
            logger.error(f"Failed to rename key {old_key} to {new_key}: {e}")
            raise

    async def set_expire(self, key: str, ttl: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 键名
            ttl: 过期时间（秒），-1表示永不过期
            
        Returns:
            是否成功
        """
        try:
            if not await self.client.exists(key):
                raise ValueError(f"Key '{key}' does not exist")

            if ttl == -1:
                await self.client.persist(key)
            else:
                await self.client.expire(key, ttl)

            return True

        except Exception as e:
            logger.error(f"Failed to set expire for key {key}: {e}")
            raise

    async def flush_db(self, confirm: bool = False) -> bool:
        """
        清空当前数据库
        
        Args:
            confirm: 确认清空
            
        Returns:
            是否成功
        """
        if not confirm:
            raise ValueError("Must confirm to flush database")

        try:
            await self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Failed to flush database: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.aclose()
