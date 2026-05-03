#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库管理API（异步版本）
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query

from core.database_manager.schema import (
    DatabaseConfig,
    DatabaseInfo,
    DatabaseCreateIn,
    DatabaseOperationOut,
    SchemaInfo,
    TableInfo,
    TableStructure,
    ColumnInfo,
    IndexInfo,
    ConstraintInfo,
    ViewInfo,
    ViewStructure,
    QueryDataIn,
    QueryDataOut,
    ExecuteSQLIn,
    ExecuteSQLOut,
    InsertDataIn,
    UpdateDataIn,
    DeleteDataIn,
    DataOperationOut,
    ExecuteDDLIn,
    ExecuteDDLOut
)
from core.database_manager.service import AsyncDatabaseManagerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/database_manager", tags=["数据库管理"])


# ============ 数据库配置 ============
@router.get("/configs", response_model=List[DatabaseConfig], summary="获取数据库配置列表")
async def get_database_configs():
    """获取所有配置的数据库信息"""
    return AsyncDatabaseManagerService.get_database_configs()


@router.post("/{db_name}/test", summary="测试数据库连接")
async def test_database_connection(db_name: str):
    """测试指定数据库的连接"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.test_connection()


# ============ 数据库管理 ============
@router.get("/{db_name}/databases", response_model=List[DatabaseInfo], summary="获取数据库列表")
async def get_databases(db_name: str):
    """获取所有数据库"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.get_databases()


@router.post("/{db_name}/databases", response_model=DatabaseOperationOut, summary="创建数据库")
async def create_database(db_name: str, data: DatabaseCreateIn):
    """创建新数据库"""
    try:
        service = AsyncDatabaseManagerService(db_name)
        success = await service.create_database(
            name=data.name,
            owner=data.owner,
            encoding=data.encoding,
            template=data.template
        )
        return DatabaseOperationOut(
            success=success,
            message="数据库创建成功" if success else "数据库创建失败"
        )
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return DatabaseOperationOut(success=False, message=str(e))


@router.delete("/{db_name}/databases/{database_name}", response_model=DatabaseOperationOut, summary="删除数据库")
async def drop_database(db_name: str, database_name: str):
    """删除数据库"""
    try:
        service = AsyncDatabaseManagerService(db_name)
        success = await service.drop_database(database_name)
        return DatabaseOperationOut(
            success=success,
            message="数据库删除成功" if success else "数据库删除失败"
        )
    except Exception as e:
        logger.error(f"Failed to drop database: {e}")
        return DatabaseOperationOut(success=False, message=str(e))


# ============ Schema管理（PostgreSQL） ============
@router.get("/{db_name}/schemas", response_model=List[SchemaInfo], summary="获取Schema列表")
async def get_schemas(db_name: str, database: str = None):
    """获取所有Schema（仅PostgreSQL）"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.get_schemas(database)


# ============ 表管理 ============
@router.get("/{db_name}/tables", response_model=List[TableInfo], summary="获取表列表")
async def get_tables(
    db_name: str,
    database: str = Query(None, description="数据库名"),
    schema_name: str = Query(None, description="Schema名")
):
    """获取指定schema/database的所有表"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    return await service.get_tables(database=database, schema_name=schema_name)


@router.get("/{db_name}/tables/{table_name}/structure", response_model=TableStructure, summary="获取表结构")
async def get_table_structure(
    db_name: str,
    table_name: str,
    database: str = Query(None, description="数据库名"),
    schema_name: str = Query(None, description="Schema名")
):
    """获取表的详细结构"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    try:
        return await service.get_table_structure(table_name, database=database, schema_name=schema_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{db_name}/tables/{table_name}/ddl", summary="获取表DDL")
async def get_table_ddl(
    db_name: str,
    table_name: str,
    database: str = Query(None, description="数据库名"),
    schema_name: str = Query(None, description="Schema名")
):
    """获取表的DDL语句"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    ddl = await service.get_table_ddl(table_name, schema_name)
    return {"ddl": ddl}


@router.get("/{db_name}/tables/{table_name}/columns", response_model=List[ColumnInfo], summary="获取表字段")
async def get_table_columns(
    db_name: str,
    table_name: str,
    schema_name: str = Query(None, description="Schema名")
):
    """获取表的字段信息"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    return await service.get_table_columns(table_name, schema_name)


@router.get("/{db_name}/tables/{table_name}/indexes", response_model=List[IndexInfo], summary="获取表索引")
async def get_table_indexes(
    db_name: str,
    table_name: str,
    schema_name: str = Query(None, description="Schema名")
):
    """获取表的索引信息"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    return await service.get_table_indexes(table_name, schema_name)


@router.get("/{db_name}/tables/{table_name}/constraints", response_model=List[ConstraintInfo], summary="获取表约束")
async def get_table_constraints(
    db_name: str,
    table_name: str,
    schema_name: str = Query(None, description="Schema名")
):
    """获取表的约束信息"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    return await service.get_table_constraints(table_name, schema_name)


# ============ 视图管理 ============
@router.get("/{db_name}/views", response_model=List[ViewInfo], summary="获取视图列表")
async def get_views(
    db_name: str,
    database: str = Query(None, description="数据库名"),
    schema_name: str = Query(None, description="Schema名")
):
    """获取指定schema/database的所有视图"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    return await service.get_views(database=database, schema_name=schema_name)


@router.get("/{db_name}/views/{view_name}/structure", response_model=ViewStructure, summary="获取视图结构")
async def get_view_structure(
    db_name: str,
    view_name: str,
    schema_name: str = Query(None, description="Schema名")
):
    """获取视图的详细结构"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    try:
        return await service.get_view_structure(view_name, schema_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{db_name}/views/{view_name}/definition", summary="获取视图定义")
async def get_view_definition(
    db_name: str,
    view_name: str,
    schema_name: str = Query(None, description="Schema名")
):
    """获取视图的定义SQL"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    definition = await service.get_view_definition(view_name, schema_name)
    return {"definition": definition}


@router.get("/{db_name}/views/{view_name}/dependencies", response_model=List[str], summary="获取视图依赖")
async def get_view_dependencies(
    db_name: str,
    view_name: str,
    schema_name: str = Query(None, description="Schema名")
):
    """获取视图依赖的表列表"""
    service = AsyncDatabaseManagerService(db_name)

    if not schema_name:
        schema_name = 'public'

    return await service.get_view_dependencies(view_name, schema_name)


# ============ 数据查询 ============
@router.post("/{db_name}/query", response_model=QueryDataOut, summary="查询表数据")
async def query_data(db_name: str, data: QueryDataIn):
    """分页查询表数据"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.query_data(
        table_name=data.table_name,
        schema_name=data.schema_name,
        page=data.page,
        page_size=data.page_size,
        where=data.where,
        order_by=data.order_by
    )


# ============ SQL执行 ============
@router.post("/{db_name}/execute", response_model=ExecuteSQLOut, summary="执行SQL")
async def execute_sql(db_name: str, data: ExecuteSQLIn):
    """执行自定义SQL语句"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.execute_sql(data.sql, data.is_query)


# ============ 数据操作 ============
@router.post("/{db_name}/data/insert", response_model=DataOperationOut, summary="插入数据")
async def insert_data(db_name: str, data: InsertDataIn):
    """向表中插入数据"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.insert_data(data.table_name, data.data, data.schema_name)


@router.post("/{db_name}/data/update", response_model=DataOperationOut, summary="更新数据")
async def update_data(db_name: str, data: UpdateDataIn):
    """更新表中的数据"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.update_data(data.table_name, data.data, data.where, data.schema_name)


@router.post("/{db_name}/data/delete", response_model=DataOperationOut, summary="删除数据")
async def delete_data(db_name: str, data: DeleteDataIn):
    """删除表中的数据"""
    service = AsyncDatabaseManagerService(db_name)
    return await service.delete_data(data.table_name, data.where, data.schema_name)


# ============ DDL操作 ============
@router.post("/{db_name}/execute/ddl", response_model=ExecuteDDLOut, summary="执行DDL语句")
async def execute_ddl(db_name: str, data: ExecuteDDLIn):
    """执行DDL语句（CREATE TABLE, ALTER TABLE, DROP TABLE等）"""
    service = AsyncDatabaseManagerService(db_name)
    result = await service.execute_ddl(data.sql, data.database, data.schema_name)
    return ExecuteDDLOut(**result)
