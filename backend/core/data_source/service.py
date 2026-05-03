#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Source Service - 数据源服务
提供数据源执行、缓存、转换等核心功能（异步版本）

数据权限：
- 使用 get_list_with_data_scope() 自动应用数据权限
- 支持本人、本部门、本部门及下级、全部等数据范围
"""
import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from utils.redis import RedisClient
from core.data_source.model import DataSource
from app.data_scope_utils import get_data_scope_filter, apply_data_scope_to_conditions

logger = logging.getLogger(__name__)

# 资源类型（用于数据权限配置）
RESOURCE_TYPE = "data_source"
RESOURCE_DISPLAY_NAME = "数据源管理"


class DataSourceService:
    """数据源服务类"""

    # SQL 危险关键词（禁止执行）
    DANGEROUS_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]

    # 数据量限制
    MAX_ROWS_EXECUTE = 1000  # 正常执行最多返回 1000 条
    MAX_ROWS_TEST = 100  # 测试最多返回 100 条

    # ==================== CRUD 方法 ====================

    @classmethod
    async def get_list(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        application_id: str = None,
        name: str = None,
        code: str = None,
        source_type: str = None,
        status: bool = None,
    ) -> Tuple[List[DataSource], int]:
        """获取数据源列表"""
        stmt = select(DataSource).where(DataSource.is_deleted == False)

        # 应用过滤
        if application_id:
            stmt = stmt.where(DataSource.application_id == application_id)
        else:
            stmt = stmt.where(DataSource.application_id.is_(None))

        if name:
            stmt = stmt.where(DataSource.name.contains(name))
        if code:
            stmt = stmt.where(DataSource.code.contains(code))
        if source_type:
            stmt = stmt.where(DataSource.source_type == source_type)
        if status is not None:
            stmt = stmt.where(DataSource.status == status)

        # 计算总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页
        stmt = stmt.order_by(DataSource.sort.desc(), DataSource.sys_create_datetime.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @classmethod
    async def get_list_with_data_scope(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        application_id: str = None,
        name: str = None,
        code: str = None,
        source_type: str = None,
        status: bool = None,
    ) -> Tuple[List[DataSource], int]:
        """
        获取数据源列表（带数据权限过滤）
        
        自动从上下文获取当前用户信息，应用数据权限过滤
        """
        conditions = [DataSource.is_deleted == False]

        # 应用过滤
        if application_id:
            conditions.append(DataSource.application_id == application_id)
        else:
            conditions.append(DataSource.application_id.is_(None))

        if name:
            conditions.append(DataSource.name.contains(name))
        if code:
            conditions.append(DataSource.code.contains(code))
        if source_type:
            conditions.append(DataSource.source_type == source_type)
        if status is not None:
            conditions.append(DataSource.status == status)

        # 获取数据权限过滤条件并应用
        data_scope_filter = await get_data_scope_filter(db, RESOURCE_TYPE)
        scope_conditions = apply_data_scope_to_conditions(DataSource, data_scope_filter)
        conditions.extend(scope_conditions)

        # 计算总数
        count_stmt = select(func.count()).select_from(
            select(DataSource).where(and_(*conditions)).subquery()
        )
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页
        stmt = select(DataSource).where(and_(*conditions))
        stmt = stmt.order_by(DataSource.sort.desc(), DataSource.sys_create_datetime.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @classmethod
    async def get_all(cls, db: AsyncSession, application_id: str = None) -> List[DataSource]:
        """获取所有启用的数据源"""
        conditions = [
            DataSource.is_deleted == False,
            DataSource.status == True,
        ]
        if application_id:
            conditions.append(DataSource.application_id == application_id)
        else:
            conditions.append(DataSource.application_id.is_(None))
        
        stmt = select(DataSource).where(*conditions).order_by(DataSource.sort.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(cls, db: AsyncSession, source_id: str) -> Optional[DataSource]:
        """根据ID获取数据源"""
        stmt = select(DataSource).where(
            DataSource.id == source_id,
            DataSource.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_code(cls, db: AsyncSession, code: str) -> Optional[DataSource]:
        """根据编码获取数据源"""
        stmt = select(DataSource).where(
            DataSource.code == code,
            DataSource.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db: AsyncSession, data: dict) -> DataSource:
        """创建数据源"""
        from utils.context import get_current_user_info_from_context
        
        source = DataSource(**data)
        
        # 自动填充创建人和部门
        user_info = get_current_user_info_from_context()
        if user_info:
            if not source.sys_creator_id:
                source.sys_creator_id = user_info.get('user_id')
            if not source.sys_dept_id and user_info.get('dept_id'):
                source.sys_dept_id = user_info.get('dept_id')
        
        db.add(source)
        await db.flush()
        await db.refresh(source)
        return source

    @classmethod
    async def update(cls, db: AsyncSession, source_id: str, data: dict) -> Optional[DataSource]:
        """更新数据源"""
        source = await cls.get_by_id(db, source_id)
        if not source:
            return None

        old_code = source.code
        for key, value in data.items():
            if value is not None and hasattr(source, key):
                setattr(source, key, value)

        db.add(source)
        await db.flush()
        await db.refresh(source)

        # 清除缓存
        await cls.clear_cache(old_code)
        if source.code != old_code:
            await cls.clear_cache(source.code)

        return source

    @classmethod
    async def delete(cls, db: AsyncSession, source_id: str) -> bool:
        """删除数据源（软删除）"""
        source = await cls.get_by_id(db, source_id)
        if not source:
            return False

        source.is_deleted = True
        db.add(source)
        await db.flush()

        # 清除缓存
        await cls.clear_cache(source.code)
        return True

    @classmethod
    async def check_code_exists(cls, db: AsyncSession, code: str, exclude_id: str = None) -> bool:
        """检查编码是否存在"""
        stmt = select(DataSource).where(DataSource.code == code)
        if exclude_id:
            stmt = stmt.where(DataSource.id != exclude_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def copy(cls, db: AsyncSession, source_id: str, new_code: str, new_name: str = None) -> Optional[DataSource]:
        """复制数据源"""
        source = await cls.get_by_id(db, source_id)
        if not source:
            return None

        # 创建副本
        new_source = DataSource(
            name=new_name or f"{source.name}(副本)",
            code=new_code,
            source_type=source.source_type,
            description=source.description,
            status=source.status,
            api_url=source.api_url,
            api_method=source.api_method,
            api_headers=source.api_headers,
            api_query_params=source.api_query_params,
            api_body_type=source.api_body_type,
            api_body=source.api_body,
            api_content_type=source.api_content_type,
            api_timeout=source.api_timeout,
            api_data_path=source.api_data_path,
            api_auth_type=source.api_auth_type,
            api_auth_config=source.api_auth_config,
            api_retry_count=source.api_retry_count,
            api_retry_interval=source.api_retry_interval,
            api_success_condition=source.api_success_condition,
            api_proxy=source.api_proxy,
            api_follow_redirects=source.api_follow_redirects,
            api_verify_ssl=source.api_verify_ssl,
            sql_content=source.sql_content,
            db_connection=source.db_connection,
            static_data=source.static_data,
            params=source.params,
            result_type=source.result_type,
            tree_config=source.tree_config,
            field_mapping=source.field_mapping,
            chart_config=source.chart_config,
            cache_enabled=source.cache_enabled,
            cache_ttl=source.cache_ttl,
        )
        db.add(new_source)
        await db.flush()
        await db.refresh(new_source)
        return new_source

    # ==================== 执行方法 ====================

    @classmethod
    async def execute(cls, db: AsyncSession, code: str, params: Dict[str, Any] = None) -> Any:
        """根据编码执行数据源"""
        source = await cls.get_by_code(db, code)
        if not source or not source.status:
            raise ValueError(f"数据源不存在或已禁用: {code}")
        return await cls.execute_source(db, source, params)

    @classmethod
    async def execute_by_id(cls, db: AsyncSession, source_id: str, params: Dict[str, Any] = None) -> Any:
        """根据ID执行数据源"""
        source = await cls.get_by_id(db, source_id)
        if not source or not source.status:
            raise ValueError("数据源不存在或已禁用")
        return await cls.execute_source(db, source, params)

    @classmethod
    async def execute_source(cls, db: AsyncSession, source: DataSource, params: Dict[str, Any] = None) -> Any:
        """执行数据源对象"""
        params = params or {}

        # 合并默认参数
        final_params = cls._merge_params(source.params or [], params)

        # 检查缓存
        if source.cache_enabled:
            cache_key = cls._get_cache_key(source.code, final_params)
            cached = await cls._get_cache(cache_key)
            if cached is not None:
                logger.debug(f"数据源 {source.code} 命中缓存")
                return cached

        # 根据类型执行
        if source.source_type == 'sql':
            result = await cls._execute_sql(db, source, final_params)
        elif source.source_type == 'api':
            result = await cls._execute_api(source, final_params)
        else:
            result = source.static_data or []

        # 字段映射
        if source.field_mapping:
            result = cls._apply_field_mapping(result, source.field_mapping)

        # 结果转换
        result = cls._transform_result(result, source)

        # 限制返回数据量
        if isinstance(result, list) and len(result) > cls.MAX_ROWS_EXECUTE:
            logger.warning(f"数据源 {source.code} 返回数据超过限制，截取前 {cls.MAX_ROWS_EXECUTE} 条")
            result = result[:cls.MAX_ROWS_EXECUTE]

        # 写入缓存
        if source.cache_enabled and source.cache_ttl > 0:
            cache_key = cls._get_cache_key(source.code, final_params)
            await cls._set_cache(cache_key, result, source.cache_ttl)
            logger.debug(f"数据源 {source.code} 结果已缓存 {source.cache_ttl}s")

        return result

    @classmethod
    async def execute_temp(cls, db: AsyncSession, config: Dict[str, Any], params: Dict[str, Any] = None) -> Any:
        """执行临时配置（用于测试/预览）"""
        params = params or {}

        # 合并默认参数
        params_def = config.get('params_def', [])
        final_params = cls._merge_params(params_def, params)

        source_type = config.get('source_type', 'static')

        # 根据类型执行
        if source_type == 'sql':
            result = await cls._execute_sql_temp(db, config, final_params)
        elif source_type == 'api':
            result = await cls._execute_api_temp(config, final_params)
        else:
            result = config.get('static_data', [])

        # 字段映射
        field_mapping = config.get('field_mapping', {})
        if field_mapping:
            result = cls._apply_field_mapping(result, field_mapping)

        # 结果转换
        result = cls._transform_result_temp(result, config)

        # 测试时限制返回数据量
        if isinstance(result, list) and len(result) > cls.MAX_ROWS_TEST:
            result = result[:cls.MAX_ROWS_TEST]

        return result

    # ==================== SQL 执行 ====================

    @classmethod
    async def _execute_sql(cls, db: AsyncSession, source: DataSource, params: Dict[str, Any]) -> List[Dict]:
        """执行 SQL 查询"""
        sql = (source.sql_content or '').strip()
        return await cls._execute_sql_internal(db, sql, params)

    @classmethod
    async def _execute_sql_temp(cls, db: AsyncSession, config: Dict[str, Any], params: Dict[str, Any]) -> List[Dict]:
        """执行临时 SQL 查询"""
        sql = config.get('sql_content', '').strip()
        return await cls._execute_sql_internal(db, sql, params)

    @classmethod
    def _expand_date_params(cls, sql: str, params: Dict[str, Any]) -> tuple:
        """将 date 类型参数的 = 比较自动展开为范围查询，使 date 参数可匹配 datetime/timestamp 字段"""
        from datetime import date, datetime as dt, timedelta
        date_param_names = [
            k for k, v in params.items()
            if isinstance(v, date) and not isinstance(v, dt)
        ]
        if not date_param_names:
            return sql, params

        new_sql = sql
        new_params = dict(params)
        for name in date_param_names:
            pattern = re.compile(
                r'(\w+(?:\.\w+)?)'
                r'\s*=\s*'
                r':' + re.escape(name) + r'\b',
                re.IGNORECASE,
            )
            match = pattern.search(new_sql)
            if match:
                col = match.group(1)
                start_key = f'{name}__start'
                end_key = f'{name}__end'
                replacement = f'{col} >= :{start_key} AND {col} < :{end_key}'
                new_sql = new_sql[:match.start()] + replacement + new_sql[match.end():]
                d = new_params.pop(name)
                new_params[start_key] = dt(d.year, d.month, d.day, 0, 0, 0)
                new_params[end_key] = dt(d.year, d.month, d.day, 0, 0, 0) + timedelta(days=1)

        return new_sql, new_params

    @classmethod
    async def _execute_sql_internal(cls, db: AsyncSession, sql: str, params: Dict[str, Any]) -> List[Dict]:
        """内部 SQL 执行方法"""
        if not sql:
            return []

        # 安全检查：只允许 SELECT
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            raise ValueError('只允许 SELECT 或 WITH 查询')

        # 禁止危险关键词
        for keyword in cls.DANGEROUS_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                raise ValueError(f'SQL 中不允许使用 {keyword}')

        # date 参数自动展开为范围查询，兼容 datetime/timestamp 字段
        sql, params = cls._expand_date_params(sql, params)

        # 将 :param 格式转换为 SQLAlchemy 格式
        from sqlalchemy import text
        try:
            result = await db.execute(text(sql), params)
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"SQL 执行失败: {str(e)}")
            raise ValueError(f"SQL 执行失败: {str(e)}")

    # ==================== API 执行 ====================

    @classmethod
    async def _execute_api(cls, source: DataSource, params: Dict[str, Any]) -> Any:
        """执行 API 请求"""
        return await cls._execute_api_internal(
            url=source.api_url or '',
            method=source.api_method or 'GET',
            headers=source.api_headers or {},
            query_params=source.api_query_params or [],
            body_type=source.api_body_type or 'none',
            body=source.api_body or {},
            content_type=source.api_content_type or '',
            timeout=source.api_timeout or 30,
            data_path=source.api_data_path or '',
            auth_type=source.api_auth_type or 'none',
            auth_config=source.api_auth_config or {},
            retry_count=source.api_retry_count or 0,
            retry_interval=source.api_retry_interval or 1,
            success_condition=source.api_success_condition or {},
            proxy=source.api_proxy or '',
            follow_redirects=source.api_follow_redirects if source.api_follow_redirects is not None else True,
            verify_ssl=source.api_verify_ssl if source.api_verify_ssl is not None else True,
            params=params
        )

    @classmethod
    async def _execute_api_temp(cls, config: Dict[str, Any], params: Dict[str, Any]) -> Any:
        """执行临时 API 请求"""
        return await cls._execute_api_internal(
            url=config.get('api_url', ''),
            method=config.get('api_method', 'GET'),
            headers=config.get('api_headers', {}),
            query_params=config.get('api_query_params', []),
            body_type=config.get('api_body_type', 'none'),
            body=config.get('api_body', {}),
            content_type=config.get('api_content_type', ''),
            timeout=config.get('api_timeout', 30),
            data_path=config.get('api_data_path', ''),
            auth_type=config.get('api_auth_type', 'none'),
            auth_config=config.get('api_auth_config', {}),
            retry_count=config.get('api_retry_count', 0),
            retry_interval=config.get('api_retry_interval', 1),
            success_condition=config.get('api_success_condition', {}),
            proxy=config.get('api_proxy', ''),
            follow_redirects=config.get('api_follow_redirects', True),
            verify_ssl=config.get('api_verify_ssl', True),
            params=params
        )

    @classmethod
    async def _execute_api_internal(
            cls,
            url: str,
            method: str,
            headers: Dict[str, str],
            body: Dict[str, Any],
            timeout: int,
            data_path: str,
            params: Dict[str, Any],
            query_params: List = None,
            body_type: str = 'none',
            content_type: str = '',
            auth_type: str = 'none',
            auth_config: Dict[str, Any] = None,
            retry_count: int = 0,
            retry_interval: int = 1,
            success_condition: Dict[str, Any] = None,
            proxy: str = '',
            follow_redirects: bool = True,
            verify_ssl: bool = True,
    ) -> Any:
        """内部 API 执行方法"""
        import asyncio
        if not url:
            return []

        query_params = query_params or []
        auth_config = auth_config or {}
        success_condition = success_condition or {}

        # 替换 URL 中的参数占位符 {param}
        for key, value in params.items():
            url = url.replace(f'{{{key}}}', str(value) if value is not None else '')

        # 处理请求头中的参数
        final_headers = {}
        for k, v in headers.items():
            if isinstance(v, str):
                for pk, pv in params.items():
                    v = v.replace(f'{{{pk}}}', str(pv) if pv is not None else '')
            final_headers[k] = v

        # 处理认证
        cls._apply_auth(final_headers, auth_type, auth_config, params)

        # 处理 Query 参数（合并可视化配置的和URL传入的）
        final_query_params = dict(params)  # 从参数定义中的默认值开始
        logger.debug(f"[DataSource] Initial params: {params}")
        for qp in query_params:
            if qp.get('enabled', True) and qp.get('key'):
                val = qp.get('value', '')
                original_val = val
                if isinstance(val, str):
                    for pk, pv in params.items():
                        val = val.replace(f'{{{pk}}}', str(pv) if pv is not None else '')
                logger.debug(f"[DataSource] Query param {qp['key']}: {original_val} -> {val}")
                final_query_params[qp['key']] = val
        logger.debug(f"[DataSource] Final query params: {final_query_params}")

        # 构建 httpx 客户端参数
        client_kwargs = {
            'timeout': timeout,
            'follow_redirects': follow_redirects,
            'verify': verify_ssl,
        }
        if proxy:
            client_kwargs['proxy'] = proxy

        last_error = None
        max_attempts = max(1, retry_count + 1)

        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(**client_kwargs) as client:
                    method_upper = method.upper()

                    if method_upper == 'GET':
                        resp = await client.get(url, params=final_query_params, headers=final_headers)
                    else:
                        # 根据 body_type 构建请求
                        req_kwargs = {'headers': final_headers, 'params': final_query_params}

                        if body_type == 'json' or (body_type == 'none' and body):
                            final_body = cls._replace_params_in_dict(body.copy() if body else {}, params)
                            req_kwargs['json'] = final_body
                        elif body_type == 'form-data':
                            final_body = cls._replace_params_in_dict(body.copy() if body else {}, params)
                            req_kwargs['data'] = final_body
                        elif body_type == 'x-www-form-urlencoded':
                            final_body = cls._replace_params_in_dict(body.copy() if body else {}, params)
                            req_kwargs['data'] = final_body
                            final_headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
                        elif body_type == 'raw':
                            import json
                            raw_body = json.dumps(body) if isinstance(body, dict) else str(body)
                            for pk, pv in params.items():
                                raw_body = raw_body.replace(f'{{{pk}}}', str(pv) if pv is not None else '')
                            req_kwargs['content'] = raw_body.encode('utf-8')
                            if content_type:
                                final_headers['Content-Type'] = content_type

                        resp = await client.request(method_upper, url, **req_kwargs)

                    # 检查成功条件
                    expected_codes = success_condition.get('status_codes')
                    if expected_codes and isinstance(expected_codes, list):
                        if resp.status_code not in expected_codes:
                            raise ValueError(f"HTTP 状态码 {resp.status_code} 不在预期范围 {expected_codes} 内")
                    else:
                        resp.raise_for_status()

                    result = resp.json()

                    # 检查字段级成功条件
                    field_path = success_condition.get('field_path')
                    field_value = success_condition.get('field_value')
                    if field_path:
                        actual_value = cls._get_nested_value(result, field_path)
                        if field_value is not None and str(actual_value) != str(field_value):
                            raise ValueError(f"响应字段 {field_path} 的值 {actual_value} 不等于预期值 {field_value}")

                    # 提取数据路径
                    if data_path:
                        result = cls._get_nested_value(result, data_path)

                    return result if result is not None else []

            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    logger.warning(f"API 请求第 {attempt + 1} 次失败，{retry_interval}s 后重试: {str(e)}")
                    await asyncio.sleep(retry_interval)
                    continue
                break

        logger.error(f"API 请求失败（共 {max_attempts} 次尝试）: {str(last_error)}")
        raise ValueError(f"API 请求失败: {str(last_error)}")

    @classmethod
    def _apply_auth(
            cls,
            headers: Dict[str, str],
            auth_type: str,
            auth_config: Dict[str, Any],
            params: Dict[str, Any]
    ):
        """应用认证配置到请求头"""
        if auth_type == 'none' or not auth_config:
            return

        def _resolve(val: str) -> str:
            if isinstance(val, str):
                for pk, pv in params.items():
                    val = val.replace(f'{{{pk}}}', str(pv) if pv is not None else '')
            return val

        if auth_type == 'bearer_token':
            token = _resolve(auth_config.get('token', ''))
            if token:
                headers['Authorization'] = f'Bearer {token}'

        elif auth_type == 'basic_auth':
            import base64
            username = _resolve(auth_config.get('username', ''))
            password = _resolve(auth_config.get('password', ''))
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'

        elif auth_type == 'api_key':
            key_name = auth_config.get('key_name', '')
            key_value = _resolve(auth_config.get('key_value', ''))
            key_position = auth_config.get('key_position', 'header')  # header / query
            if key_name and key_value:
                if key_position == 'header':
                    headers[key_name] = key_value
                # query 位置的 key 在 query_params 中处理

    # ==================== 结果转换 ====================

    @classmethod
    def _transform_result(cls, data: Any, source: DataSource) -> Any:
        """转换结果格式"""
        return cls._transform_result_internal(
            data=data,
            result_type=source.result_type or 'list',
            tree_config=source.tree_config or {},
            chart_config=source.chart_config or {}
        )

    @classmethod
    def _transform_result_temp(cls, data: Any, config: Dict[str, Any]) -> Any:
        """转换临时结果格式"""
        return cls._transform_result_internal(
            data=data,
            result_type=config.get('result_type', 'list'),
            tree_config=config.get('tree_config', {}),
            chart_config=config.get('chart_config', {})
        )

    @classmethod
    def _transform_result_internal(
            cls,
            data: Any,
            result_type: str,
            tree_config: Dict[str, Any],
            chart_config: Dict[str, Any] = None
    ) -> Any:
        """内部结果转换方法"""
        if not isinstance(data, list):
            return data

        if result_type == 'tree':
            return cls._list_to_tree(
                data,
                id_field=tree_config.get('id_field', 'id'),
                parent_field=tree_config.get('parent_field', 'parent_id'),
                children_field=tree_config.get('children_field', 'children'),
                root_value=tree_config.get('root_value', None),
            )
        elif result_type == 'object':
            return data[0] if data else None
        elif result_type == 'value':
            if data and len(data) > 0:
                first_row = data[0]
                if isinstance(first_row, dict) and len(first_row) > 0:
                    return list(first_row.values())[0]
            return None
        elif result_type == 'chart-axis':
            return cls._transform_to_chart_axis(data, chart_config or {})
        elif result_type == 'chart-pie':
            return cls._transform_to_chart_pie(data, chart_config or {})
        elif result_type == 'chart-gauge':
            return cls._transform_to_chart_gauge(data, chart_config or {})
        elif result_type == 'chart-radar':
            return cls._transform_to_chart_radar(data, chart_config or {})
        elif result_type == 'chart-scatter':
            return cls._transform_to_chart_scatter(data, chart_config or {})
        elif result_type == 'chart-heatmap':
            return cls._transform_to_chart_heatmap(data, chart_config or {})

        return data

    @classmethod
    def _transform_to_chart_axis(cls, data: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为轴向图表数据格式"""
        if not data:
            return {"xAxisData": [], "seriesData": []}

        x_field = config.get('x_field', '')
        series_fields = config.get('series_fields', [])
        series_names = config.get('series_names', [])

        if not x_field or not series_fields:
            if data and isinstance(data[0], dict):
                keys = list(data[0].keys())
                if not x_field and keys:
                    x_field = keys[0]
                if not series_fields and len(keys) > 1:
                    series_fields = keys[1:]

        x_axis_data = [item.get(x_field, '') for item in data]

        series_data = []
        for i, field in enumerate(series_fields):
            name = series_names[i] if i < len(series_names) else field
            values = [item.get(field, 0) for item in data]
            series_data.append({"name": name, "data": values})

        return {"xAxisData": x_axis_data, "seriesData": series_data}

    @classmethod
    def _transform_to_chart_pie(cls, data: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为饼图数据格式"""
        if not data:
            return {"seriesData": []}

        name_field = config.get('name_field', '')
        value_field = config.get('value_field', '')

        if not name_field or not value_field:
            if data and isinstance(data[0], dict):
                keys = list(data[0].keys())
                if len(keys) >= 2:
                    if not name_field:
                        name_field = keys[0]
                    if not value_field:
                        value_field = keys[1]

        series_data = []
        for item in data:
            series_data.append({
                "name": item.get(name_field, ''),
                "value": item.get(value_field, 0)
            })

        return {"seriesData": series_data}

    @classmethod
    def _transform_to_chart_gauge(cls, data: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为仪表盘数据格式"""
        if not data:
            return {"value": 0, "name": "", "max": 100}

        value_field = config.get('value_field', 'value')
        name_field = config.get('name_field', 'name')
        max_field = config.get('max_field', 'max')

        first_row = data[0] if data else {}

        return {
            "value": first_row.get(value_field, 0),
            "name": first_row.get(name_field, ''),
            "max": first_row.get(max_field, 100)
        }

    @classmethod
    def _transform_to_chart_radar(cls, data: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为雷达图数据格式"""
        if not data:
            return {"indicator": [], "seriesData": []}

        indicator_field = config.get('indicator_field', 'name')
        max_field = config.get('max_field', 'max')
        value_fields = config.get('value_fields', [])
        series_names = config.get('series_names', [])

        if not value_fields and data:
            keys = list(data[0].keys())
            value_fields = [k for k in keys if k not in [indicator_field, max_field]]

        indicator = []
        for item in data:
            indicator.append({
                "name": item.get(indicator_field, ''),
                "max": item.get(max_field, 100)
            })

        series_data = []
        for i, field in enumerate(value_fields):
            name = series_names[i] if i < len(series_names) else field
            values = [item.get(field, 0) for item in data]
            series_data.append({"name": name, "value": values})

        return {"indicator": indicator, "seriesData": series_data}

    @classmethod
    def _transform_to_chart_scatter(cls, data: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为散点图数据格式"""
        if not data:
            return {"seriesData": []}

        x_field = config.get('x_field', 'x')
        y_field = config.get('y_field', 'y')
        size_field = config.get('size_field', '')
        name_field = config.get('name_field', '')

        series_data = []
        for item in data:
            point = [item.get(x_field, 0), item.get(y_field, 0)]
            if size_field:
                point.append(item.get(size_field, 0))
            if name_field:
                point.append(item.get(name_field, ''))
            series_data.append(point)

        return {"seriesData": series_data}

    @classmethod
    def _transform_to_chart_heatmap(cls, data: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
        """转换为热力图数据格式"""
        if not data:
            return {"xAxisData": [], "yAxisData": [], "seriesData": []}

        x_field = config.get('x_field', 'x')
        y_field = config.get('y_field', 'y')
        value_field = config.get('value_field', 'value')

        x_values = list(dict.fromkeys(item.get(x_field, '') for item in data))
        y_values = list(dict.fromkeys(item.get(y_field, '') for item in data))

        x_index = {v: i for i, v in enumerate(x_values)}
        y_index = {v: i for i, v in enumerate(y_values)}

        series_data = []
        for item in data:
            x = item.get(x_field, '')
            y = item.get(y_field, '')
            value = item.get(value_field, 0)
            series_data.append([x_index.get(x, 0), y_index.get(y, 0), value])

        return {"xAxisData": x_values, "yAxisData": y_values, "seriesData": series_data}

    @classmethod
    def _list_to_tree(
            cls,
            data: List[Dict],
            id_field: str,
            parent_field: str,
            children_field: str,
            root_value: Any = None
    ) -> List[Dict]:
        """列表转树形结构"""
        if not data:
            return []

        mapping = {}
        for item in data:
            item_id = item.get(id_field)
            if item_id is not None:
                mapping[item_id] = {**item, children_field: []}

        tree = []
        for item in data:
            item_id = item.get(id_field)
            parent_id = item.get(parent_field)
            node = mapping.get(item_id)

            if node is None:
                continue

            is_root = (
                parent_id is None or
                parent_id == root_value or
                parent_id == '' or
                parent_id not in mapping
            )

            if is_root:
                tree.append(node)
            else:
                parent_node = mapping.get(parent_id)
                if parent_node:
                    parent_node[children_field].append(node)

        return tree

    # ==================== 工具方法 ====================

    @classmethod
    def _apply_field_mapping(cls, data: List[Dict], mapping: Dict[str, str]) -> List[Dict]:
        """应用字段映射"""
        if not data or not mapping:
            return data

        result = []
        for item in data:
            if not isinstance(item, dict):
                result.append(item)
                continue

            new_item = {}
            for old_key, new_key in mapping.items():
                if old_key in item:
                    new_item[new_key] = item[old_key]
            for key, value in item.items():
                if key not in mapping:
                    new_item[key] = value
            result.append(new_item)

        return result

    @classmethod
    def _merge_params(cls, param_defs: List[Dict], input_params: Dict[str, Any]) -> Dict[str, Any]:
        """合并参数"""
        result = {}

        for p in param_defs:
            name = p.get('name')
            if not name:
                continue

            param_type = p.get('type', 'string')
            required = p.get('required', False)
            default = p.get('default')

            if name in input_params:
                value = input_params[name]
                result[name] = cls._convert_param_type(value, param_type)
            elif default is not None:
                result[name] = cls._convert_param_type(default, param_type)
            elif required:
                raise ValueError(f"缺少必填参数: {name}")
            else:
                result[name] = None

        for key, value in input_params.items():
            if key not in result:
                result[key] = cls._auto_convert_param(value)

        return result

    @classmethod
    def _auto_convert_param(cls, value: Any) -> Any:
        """对未在参数定义中声明的参数，自动推断并转换常见类型（date/datetime）"""
        if value is None or not isinstance(value, str):
            return value
        s = value.strip()
        if not s:
            return value
        import re
        from datetime import date, datetime as dt
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
            try:
                return date.fromisoformat(s)
            except ValueError:
                pass
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?', s):
            try:
                return dt.fromisoformat(s)
            except ValueError:
                pass
        return value

    @classmethod
    def _convert_param_type(cls, value: Any, param_type: str) -> Any:
        """参数类型转换"""
        if value is None:
            return None

        try:
            if param_type == 'integer':
                return int(value)
            elif param_type == 'float':
                return float(value)
            elif param_type == 'boolean':
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes')
            elif param_type == 'date':
                from datetime import date, datetime as dt
                if isinstance(value, date):
                    return value
                if isinstance(value, dt):
                    return value.date()
                s = str(value).strip()[:10]
                return date.fromisoformat(s)
            elif param_type == 'datetime':
                from datetime import datetime as dt
                if isinstance(value, dt):
                    return value
                s = str(value).strip()
                return dt.fromisoformat(s)
            else:
                return str(value)
        except (ValueError, TypeError):
            return value

    @classmethod
    def _replace_params_in_dict(cls, data: Dict, params: Dict[str, Any]) -> Dict:
        """递归替换字典中的参数占位符"""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                for pk, pv in params.items():
                    value = value.replace(f'{{{pk}}}', str(pv) if pv is not None else '')
                result[key] = value
            elif isinstance(value, dict):
                result[key] = cls._replace_params_in_dict(value, params)
            elif isinstance(value, list):
                result[key] = [
                    cls._replace_params_in_dict(item, params) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    @classmethod
    def _get_nested_value(cls, data: Any, path: str) -> Any:
        """获取嵌套字典中的值"""
        if not path:
            return data

        keys = path.split('.')
        result = data

        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            elif isinstance(result, list) and key.isdigit():
                index = int(key)
                result = result[index] if 0 <= index < len(result) else None
            else:
                return None

            if result is None:
                return None

        return result

    # ==================== 缓存方法 ====================

    @classmethod
    def _get_cache_key(cls, code: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        params_str = str(sorted(params.items()))
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"datasource:{code}:{params_hash}"

    @classmethod
    async def _get_cache(cls, key: str) -> Any:
        """获取缓存"""
        try:
            import json
            client = await RedisClient.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"获取缓存失败: {str(e)}")
            return None

    @classmethod
    async def _set_cache(cls, key: str, value: Any, ttl: int) -> None:
        """设置缓存"""
        try:
            import json
            client = await RedisClient.get_client()
            await client.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as e:
            logger.warning(f"设置缓存失败: {str(e)}")

    @classmethod
    async def clear_cache(cls, code: str) -> None:
        """清除数据源缓存"""
        pattern = f"datasource:{code}:*"
        try:
            client = await RedisClient.get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await client.delete(*keys)
                logger.info(f"已清除数据源 {code} 的 {len(keys)} 个缓存")
        except Exception as e:
            logger.warning(f"清除缓存失败: {str(e)}")

    # ==================== AI SQL 生成 ====================

    @classmethod
    async def ai_generate_sql(
        cls,
        db: AsyncSession,
        user_question: str,
        db_connection: str,
        database: str = "",
        schema_name: str = "",
        selected_tables: List[str] = None,
        table_fields: Dict[str, List[Dict[str, Any]]] = None,
        table_relations: List[Dict[str, Any]] = None,
        include_table_relations: bool = True,
        model_id: str = None,
    ) -> Dict[str, Any]:
        """
        使用 AI 生成 SQL 语句
        复用 Text-to-SQL 节点的核心逻辑
        
        Args:
            db: 数据库会话
            user_question: 用户问题（自然语言描述）
            db_connection: 数据库连接名称
            database: 数据库名
            schema_name: Schema 名称
            selected_tables: 选中的表名列表
            table_fields: 表字段信息（前端传递，可选）
            table_relations: 表关系列表
            include_table_relations: 是否包含表关系信息
            model_id: LLM 模型 ID
            
        Returns:
            包含 sql, thought, params 的字典
        """
        if not user_question:
            raise ValueError("请输入查询需求")
        
        if not model_id:
            raise ValueError("请选择 AI 模型")
        
        # 直接复用 TextToSqlNode 的逻辑
        from ai_platform.nodes.builtin.text_to_sql_node import TextToSqlNode
        from ai_platform.nodes.base import NodeContext
        
        # 构建节点配置
        node = TextToSqlNode()
        node.config = {
            'user_question': user_question,
            'db_config': {
                'dbName': db_connection,
                'database': database,
                'schema': schema_name or 'public',
            },
            'selected_tables': selected_tables or [],
            'table_relations': table_relations or [],
            'include_table_relations': include_table_relations,
            'model_id': model_id,
        }
        
        # 创建临时的 NodeContext
        context = NodeContext(
            workflow_run_id='temp_ai_sql_generation',
            node_config=node.config,
            variables={},
            db_session=db,
        )
        
        try:
            # 调用 Text-to-SQL 节点的异步执行方法
            result = await node.execute_async(context)
            
            if not result.success:
                raise ValueError(result.error or "生成失败")
            
            sql = result.output.get('sql', '')
            thought = result.output.get('thought', '')
            
            # 提取参数定义
            params = cls._extract_sql_params(sql)
            
            return {
                'sql': sql,
                'thought': thought,
                'params': params,
            }
        except Exception as e:
            logger.error(f"AI 生成 SQL 失败: {str(e)}")
            raise ValueError(f"生成失败: {str(e)}")

    @classmethod
    def _extract_sql_params(cls, sql: str) -> List[Dict[str, Any]]:
        """从 SQL 中提取参数占位符，生成参数定义"""
        # 匹配 :param_name 格式的参数
        pattern = r':(\w+)'
        matches = re.findall(pattern, sql)
        
        params = []
        seen = set()
        
        for param_name in matches:
            if param_name in seen:
                continue
            seen.add(param_name)
            
            # 根据参数名推测类型和默认值
            param_type = 'string'
            default_value = None
            required = False
            
            name_lower = param_name.lower()
            
            if 'date' in name_lower or 'time' in name_lower:
                param_type = 'string'
            elif 'id' in name_lower:
                param_type = 'string'
            elif 'status' in name_lower or 'type' in name_lower:
                param_type = 'integer'
            elif 'limit' in name_lower:
                param_type = 'integer'
                default_value = 20
            elif 'offset' in name_lower:
                param_type = 'integer'
                default_value = 0
            elif 'page' in name_lower:
                param_type = 'integer'
                default_value = 1
            elif 'count' in name_lower or 'num' in name_lower:
                param_type = 'integer'
            
            # 生成显示名称
            label = param_name.replace('_', ' ').title()
            
            params.append({
                'name': param_name,
                'label': label,
                'type': param_type,
                'required': required,
                'default': default_value,
            })
        
        return params
