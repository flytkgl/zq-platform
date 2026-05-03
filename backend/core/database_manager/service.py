#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库管理服务（异步版本）
支持 PostgreSQL 和 MySQL
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.config import settings

logger = logging.getLogger(__name__)


def format_size(size_bytes: int) -> str:
    """格式化字节大小"""
    if not size_bytes:
        return "0 bytes"
    if size_bytes >= 1073741824:
        return f"{size_bytes / 1073741824:.2f} GB"
    elif size_bytes >= 1048576:
        return f"{size_bytes / 1048576:.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} bytes"


def parse_database_url(database_url: str) -> dict:
    """解析数据库URL"""
    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()
    if 'postgresql' in scheme or 'postgres' in scheme:
        db_type = 'postgresql'
        default_port = 5432
    elif 'mysql' in scheme:
        db_type = 'mysql'
        default_port = 3306
    elif 'mssql' in scheme or 'sqlserver' in scheme:
        db_type = 'sqlserver'
        default_port = 1433
    else:
        return None

    return {
        'db_type': db_type,
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or default_port,
        'user': parsed.username or '',
        'password': parsed.password or '',
        'database': parsed.path.lstrip('/') if parsed.path else ''
    }


def serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """序列化行数据"""
    for key, value in row.items():
        if hasattr(value, 'isoformat'):
            row[key] = value.isoformat()
        elif isinstance(value, bytes):
            row[key] = value.decode('utf-8', errors='replace')
        elif isinstance(value, (set, frozenset)):
            row[key] = list(value)
    return row


# ============ PostgreSQL Handler ============
class PostgreSQLHandler:
    """PostgreSQL异步处理器"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    async def connect(self, database: str = None) -> bool:
        try:
            # 如果已有连接，先关闭
            if self.conn:
                try:
                    await self.conn.close()
                except Exception:
                    pass
                self.conn = None
            
            import asyncpg
            self.conn = await asyncpg.connect(
                host=self.host, port=self.port, user=self.user,
                password=self.password, database=database or self.database, 
                timeout=10,
                command_timeout=60,  # 命令执行超时
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.conn = None
            return False

    async def close(self):
        if self.conn:
            try:
                await self.conn.close()
            except Exception as e:
                logger.warning(f"Error closing PostgreSQL connection: {e}")
            finally:
                self.conn = None

    async def get_databases(self) -> List[Dict[str, Any]]:
        try:
            if not await self.connect():
                return []
            query = """
                SELECT d.datname as name, pg_catalog.pg_get_userbyid(d.datdba) as owner,
                       pg_catalog.pg_encoding_to_char(d.encoding) as encoding, d.datcollate as collation,
                       pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname)) as size,
                       pg_catalog.pg_database_size(d.datname) as size_bytes,
                       pg_catalog.shobj_description(d.oid, 'pg_database') as description
                FROM pg_catalog.pg_database d WHERE d.datistemplate = false ORDER BY d.datname
            """
            rows = await self.conn.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []
        finally:
            await self.close()

    async def create_database(self, name: str, owner: str = None, encoding: str = "UTF8", template: str = "template0", **kwargs) -> bool:
        try:
            if not await self.connect():
                return False
            query = f'CREATE DATABASE "{name}" ENCODING \'{encoding}\' TEMPLATE {template}'
            if owner:
                query += f' OWNER "{owner}"'
            await self.conn.execute(query)
            return True
        except Exception as e:
            logger.error(f"Failed to create database {name}: {e}")
            raise
        finally:
            await self.close()

    async def drop_database(self, name: str) -> bool:
        try:
            if not await self.connect():
                return False
            await self.conn.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{name}' AND pid <> pg_backend_pid()")
            await self.conn.execute(f'DROP DATABASE "{name}"')
            return True
        except Exception as e:
            logger.error(f"Failed to drop database {name}: {e}")
            raise
        finally:
            await self.close()

    async def get_schemas(self, database: str = None) -> List[Dict[str, Any]]:
        try:
            if not await self.connect(database):
                return []
            query = """
                SELECT schema_name as name, schema_owner as owner,
                       (SELECT count(*) FROM information_schema.tables WHERE table_schema = schema_name) as tables_count
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast') ORDER BY schema_name
            """
            rows = await self.conn.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get schemas: {e}")
            return []
        finally:
            await self.close()

    async def get_tables(self, database: str = None, schema_name: str = "public") -> List[Dict[str, Any]]:
        try:
            if not await self.connect(database):
                return []
            query = """
                SELECT schemaname as schema_name, tablename as table_name, 'BASE TABLE' as table_type,
                       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
                       pg_total_relation_size(schemaname || '.' || tablename) as total_size_bytes,
                       pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as table_size,
                       pg_relation_size(schemaname || '.' || tablename) as table_size_bytes,
                       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) - pg_relation_size(schemaname || '.' || tablename)) as indexes_size,
                       (pg_total_relation_size(schemaname || '.' || tablename) - pg_relation_size(schemaname || '.' || tablename)) as indexes_size_bytes,
                       obj_description((schemaname || '.' || tablename)::regclass) as description
                FROM pg_catalog.pg_tables WHERE schemaname = $1 ORDER BY tablename
            """
            rows = await self.conn.fetch(query, schema_name)
            tables = [dict(row) for row in rows]
            for table in tables:
                try:
                    result = await self.conn.fetchval(f'SELECT count(*) FROM "{schema_name}"."{table["table_name"]}"')
                    table['row_count'] = result
                except:
                    table['row_count'] = None
            return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []
        finally:
            await self.close()

    async def get_table_columns(self, table_name: str, schema_name: str = "public") -> List[Dict[str, Any]]:
        try:
            if not await self.connect():
                return []
            query = """
                SELECT c.column_name, c.data_type, c.is_nullable = 'YES' as is_nullable, c.column_default,
                       c.character_maximum_length, c.numeric_precision, c.numeric_scale, c.ordinal_position,
                       EXISTS(SELECT 1 FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name WHERE tc.table_schema = c.table_schema AND tc.table_name = c.table_name AND kcu.column_name = c.column_name AND tc.constraint_type = 'PRIMARY KEY') as is_primary_key,
                       EXISTS(SELECT 1 FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name WHERE tc.table_schema = c.table_schema AND tc.table_name = c.table_name AND kcu.column_name = c.column_name AND tc.constraint_type = 'UNIQUE') as is_unique,
                       col_description((c.table_schema || '.' || c.table_name)::regclass, c.ordinal_position) as description
                FROM information_schema.columns c WHERE c.table_schema = $1 AND c.table_name = $2 ORDER BY c.ordinal_position
            """
            rows = await self.conn.fetch(query, schema_name, table_name)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get table columns: {e}")
            return []
        finally:
            await self.close()

    async def get_table_indexes(self, table_name: str, schema_name: str = "public") -> List[Dict[str, Any]]:
        try:
            if not await self.connect():
                return []
            query = """
                SELECT i.indexname as index_name, am.amname as index_type,
                       array_to_string(array_agg(a.attname ORDER BY k.ordinality), ', ') as columns,
                       i.indexdef as definition, ix.indisunique as is_unique, ix.indisprimary as is_primary
                FROM pg_indexes i
                JOIN pg_class c ON c.relname = i.tablename AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = i.schemaname)
                JOIN pg_index ix ON ix.indexrelid = (SELECT oid FROM pg_class WHERE relname = i.indexname AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = i.schemaname))
                JOIN pg_am am ON am.oid = (SELECT relam FROM pg_class WHERE relname = i.indexname AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = i.schemaname))
                CROSS JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS k(attnum, ordinality)
                JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
                WHERE i.schemaname = $1 AND i.tablename = $2
                GROUP BY i.indexname, am.amname, i.indexdef, ix.indisunique, ix.indisprimary ORDER BY i.indexname
            """
            rows = await self.conn.fetch(query, schema_name, table_name)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get table indexes: {e}")
            return []
        finally:
            await self.close()

    async def get_table_constraints(self, table_name: str, schema_name: str = "public") -> List[Dict[str, Any]]:
        try:
            if not await self.connect():
                return []
            query = """
                SELECT tc.constraint_name, tc.constraint_type, array_to_string(array_agg(DISTINCT kcu.column_name), ', ') as columns,
                       pg_get_constraintdef((SELECT oid FROM pg_constraint WHERE conname = tc.constraint_name AND connamespace = (SELECT oid FROM pg_namespace WHERE nspname = $1))) as definition,
                       ccu.table_name as referenced_table, array_to_string(array_agg(DISTINCT ccu.column_name), ', ') as referenced_columns
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.constraint_schema
                WHERE tc.table_schema = $1 AND tc.table_name = $2
                GROUP BY tc.constraint_name, tc.constraint_type, tc.table_schema, ccu.table_name ORDER BY tc.constraint_type, tc.constraint_name
            """
            rows = await self.conn.fetch(query, schema_name, table_name)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get table constraints: {e}")
            return []
        finally:
            await self.close()

    async def get_table_structure(self, table_name: str, database: str = None, schema_name: str = "public") -> Dict[str, Any]:
        tables = await self.get_tables(database=database, schema_name=schema_name)
        table_info = next((t for t in tables if t['table_name'] == table_name), None)
        if not table_info:
            raise ValueError(f"Table {schema_name}.{table_name} not found")
        columns = await self.get_table_columns(table_name, schema_name)
        indexes = await self.get_table_indexes(table_name, schema_name)
        constraints = await self.get_table_constraints(table_name, schema_name)
        return {"table_info": table_info, "columns": columns, "indexes": indexes, "constraints": constraints}

    async def get_table_ddl(self, table_name: str, schema_name: str = "public") -> str:
        try:
            columns = await self.get_table_columns(table_name, schema_name)
            indexes = await self.get_table_indexes(table_name, schema_name)
            constraints = await self.get_table_constraints(table_name, schema_name)
            ddl_lines = [f'CREATE TABLE "{schema_name}"."{table_name}" (']
            col_defs = []
            for col in columns:
                col_def = f'    "{col["column_name"]}" {col["data_type"]}'
                if col.get("character_maximum_length"):
                    col_def = f'    "{col["column_name"]}" {col["data_type"]}({col["character_maximum_length"]})'
                if not col["is_nullable"]:
                    col_def += " NOT NULL"
                if col.get("column_default"):
                    col_def += f' DEFAULT {col["column_default"]}'
                col_defs.append(col_def)
            for pk in [c for c in constraints if c["constraint_type"] == "PRIMARY KEY"]:
                col_defs.append(f'    PRIMARY KEY ({pk["columns"]})')
            ddl_lines.append(',\n'.join(col_defs))
            ddl_lines.append(');')
            for idx in indexes:
                if not idx["is_primary"]:
                    unique = "UNIQUE " if idx["is_unique"] else ""
                    ddl_lines.append(f'\nCREATE {unique}INDEX "{idx["index_name"]}" ON "{schema_name}"."{table_name}" ({idx["columns"]});')
            return '\n'.join(ddl_lines)
        except Exception as e:
            return f"-- 获取DDL失败: {str(e)}"

    async def get_views(self, database: str = None, schema_name: str = "public") -> List[Dict[str, Any]]:
        try:
            if not await self.connect(database):
                return []
            query = """
                SELECT table_name as view_name, table_schema as schema_name, view_definition, is_updatable = 'YES' as is_updatable, check_option, 'VIEW' as view_type
                FROM information_schema.views WHERE table_schema = $1
                UNION ALL
                SELECT matviewname as view_name, schemaname as schema_name, definition as view_definition, false as is_updatable, NULL as check_option, 'MATERIALIZED VIEW' as view_type
                FROM pg_matviews WHERE schemaname = $1 ORDER BY view_name
            """
            rows = await self.conn.fetch(query, schema_name)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get views: {e}")
            return []
        finally:
            await self.close()

    async def get_view_structure(self, view_name: str, schema_name: str = "public") -> Dict[str, Any]:
        try:
            if not await self.connect():
                raise ValueError("Failed to connect")
            view_query = "SELECT table_name as view_name, table_schema as schema_name, view_definition, is_updatable = 'YES' as is_updatable, check_option, 'VIEW' as view_type FROM information_schema.views WHERE table_schema = $1 AND table_name = $2"
            view_info = await self.conn.fetchrow(view_query, schema_name, view_name)
            view_type = "VIEW"
            if not view_info:
                matview_query = "SELECT matviewname as view_name, schemaname as schema_name, definition as view_definition, false as is_updatable, NULL as check_option, 'MATERIALIZED VIEW' as view_type FROM pg_matviews WHERE schemaname = $1 AND matviewname = $2"
                view_info = await self.conn.fetchrow(matview_query, schema_name, view_name)
                view_type = "MATERIALIZED VIEW"
            if not view_info:
                raise ValueError(f"View {schema_name}.{view_name} not found")
            view_info = dict(view_info)
            columns_query = "SELECT column_name, data_type, is_nullable = 'YES' as is_nullable, ordinal_position, col_description((table_schema || '.' || table_name)::regclass::oid, ordinal_position) as description FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2 ORDER BY ordinal_position"
            columns = [dict(c) for c in await self.conn.fetch(columns_query, schema_name, view_name)]
            deps_query = "SELECT DISTINCT ref_nsp.nspname || '.' || ref_cl.relname as table_name FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid JOIN pg_class v ON v.oid = r.ev_class JOIN pg_namespace v_nsp ON v_nsp.oid = v.relnamespace JOIN pg_class ref_cl ON ref_cl.oid = d.refobjid JOIN pg_namespace ref_nsp ON ref_nsp.oid = ref_cl.relnamespace WHERE v.relkind IN ('v', 'm') AND v_nsp.nspname = $1 AND v.relname = $2 AND ref_cl.relkind IN ('r', 'v', 'm') AND d.deptype = 'n' ORDER BY table_name"
            dependencies = [row['table_name'] for row in await self.conn.fetch(deps_query, schema_name, view_name)]
            if view_type == "MATERIALIZED VIEW":
                def_result = await self.conn.fetchval("SELECT definition FROM pg_matviews WHERE schemaname = $1 AND matviewname = $2", schema_name, view_name)
                definition_sql = f'CREATE MATERIALIZED VIEW "{schema_name}"."{view_name}" AS\n{def_result}' if def_result else f"-- 无法获取视图定义"
            else:
                def_result = await self.conn.fetchval("SELECT pg_get_viewdef($1::regclass, true)", f"{schema_name}.{view_name}")
                definition_sql = f'CREATE OR REPLACE VIEW "{schema_name}"."{view_name}" AS\n{def_result}' if def_result else f"-- 无法获取视图定义"
            return {"view_info": view_info, "columns": columns, "dependencies": dependencies, "definition_sql": definition_sql}
        except Exception as e:
            logger.error(f"Failed to get view structure: {e}")
            raise
        finally:
            await self.close()

    async def get_view_definition(self, view_name: str, schema_name: str = "public") -> str:
        try:
            if not await self.connect():
                return "-- 无法连接数据库"
            is_view = await self.conn.fetchval("SELECT 1 FROM information_schema.views WHERE table_schema = $1 AND table_name = $2", schema_name, view_name)
            if is_view:
                result = await self.conn.fetchval("SELECT pg_get_viewdef($1::regclass, true)", f"{schema_name}.{view_name}")
                definition_sql = f'CREATE OR REPLACE VIEW "{schema_name}"."{view_name}" AS\n{result}' if result else "-- 无法获取视图定义"
            else:
                result = await self.conn.fetchval("SELECT definition FROM pg_matviews WHERE schemaname = $1 AND matviewname = $2", schema_name, view_name)
                definition_sql = f'CREATE MATERIALIZED VIEW "{schema_name}"."{view_name}" AS\n{result}' if result else "-- 无法获取视图定义"
            return definition_sql
        except Exception as e:
            return f"-- 获取视图定义失败: {str(e)}"
        finally:
            await self.close()

    async def get_view_dependencies(self, view_name: str, schema_name: str = "public") -> List[str]:
        try:
            if not await self.connect():
                return []
            query = "SELECT DISTINCT ref_nsp.nspname || '.' || ref_cl.relname as table_name FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid JOIN pg_class v ON v.oid = r.ev_class JOIN pg_namespace v_nsp ON v_nsp.oid = v.relnamespace JOIN pg_class ref_cl ON ref_cl.oid = d.refobjid JOIN pg_namespace ref_nsp ON ref_nsp.oid = ref_cl.relnamespace WHERE v.relkind IN ('v', 'm') AND v_nsp.nspname = $1 AND v.relname = $2 AND ref_cl.relkind IN ('r', 'v', 'm') AND d.deptype = 'n' ORDER BY table_name"
            rows = await self.conn.fetch(query, schema_name, view_name)
            return [row['table_name'] for row in rows]
        except Exception as e:
            return []
        finally:
            await self.close()

    async def query_data(self, table_name: str, schema_name: str = None, page: int = 1, page_size: int = 20, where: str = None, order_by: str = None) -> Dict[str, Any]:
        try:
            if not await self.connect():
                return {"columns": [], "rows": [], "total": 0, "page": page, "page_size": page_size}
            schema_name = schema_name or "public"
            full_table = f'"{ schema_name}"."{table_name}"'
            count_q = f"SELECT COUNT(*) FROM {full_table}" + (f" WHERE {where}" if where else "")
            total = await self.conn.fetchval(count_q)
            offset = (page - 1) * page_size
            data_q = f"SELECT * FROM {full_table}" + (f" WHERE {where}" if where else "") + (f" ORDER BY {order_by}" if order_by else "") + f" LIMIT {page_size} OFFSET {offset}"
            rows = await self.conn.fetch(data_q)
            rows_list = [serialize_row(dict(row)) for row in rows]
            columns = list(rows_list[0].keys()) if rows_list else []
            return {"columns": columns, "rows": rows_list, "total": total, "page": page, "page_size": page_size}
        except Exception as e:
            logger.error(f"Failed to query data: {e}")
            return {"columns": [], "rows": [], "total": 0, "page": page, "page_size": page_size}
        finally:
            await self.close()

    async def execute_sql(self, sql: str, is_query: bool = True) -> Dict[str, Any]:
        start_time = time.time()
        try:
            if not await self.connect():
                return {"success": False, "message": "数据库连接失败", "columns": None, "rows": None, "affected_rows": None, "execution_time": 0}
            if is_query:
                rows = await self.conn.fetch(sql)
                execution_time = time.time() - start_time
                rows_list = [serialize_row(dict(row)) for row in rows]
                columns = list(rows_list[0].keys()) if rows_list else []
                return {"success": True, "message": f"查询成功，返回 {len(rows_list)} 行", "columns": columns, "rows": rows_list, "affected_rows": None, "execution_time": round(execution_time, 3)}
            else:
                result = await self.conn.execute(sql)
                execution_time = time.time() - start_time
                affected_rows = int(result.split()[-1]) if result and result.split()[-1].isdigit() else 0
                return {"success": True, "message": f"执行成功，影响 {affected_rows} 行", "columns": None, "rows": None, "affected_rows": affected_rows, "execution_time": round(execution_time, 3)}
        except Exception as e:
            return {"success": False, "message": str(e), "columns": None, "rows": None, "affected_rows": None, "execution_time": round(time.time() - start_time, 3)}
        finally:
            await self.close()

    async def insert_data(self, table_name: str, data: Dict[str, Any], schema_name: str = None) -> Dict[str, Any]:
        try:
            if not await self.connect():
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            schema_name = schema_name or "public"
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ', '.join([f'${i+1}' for i in range(len(values))])
            query = f'INSERT INTO "{schema_name}"."{table_name}" ({", ".join(columns)}) VALUES ({placeholders})'
            await self.conn.execute(query, *values)
            return {"success": True, "message": "插入成功", "affected_rows": 1}
        except Exception as e:
            return {"success": False, "message": str(e), "affected_rows": 0}
        finally:
            await self.close()

    async def update_data(self, table_name: str, data: Dict[str, Any], where: str, schema_name: str = None) -> Dict[str, Any]:
        try:
            if not await self.connect():
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            schema_name = schema_name or "public"
            set_clause = ', '.join([f'{k} = ${i+1}' for i, k in enumerate(data.keys())])
            query = f'UPDATE "{schema_name}"."{table_name}" SET {set_clause} WHERE {where}'
            result = await self.conn.execute(query, *data.values())
            affected_rows = int(result.split()[-1]) if result and result.split()[-1].isdigit() else 0
            return {"success": True, "message": f"更新成功，影响 {affected_rows} 行", "affected_rows": affected_rows}
        except Exception as e:
            return {"success": False, "message": str(e), "affected_rows": 0}
        finally:
            await self.close()

    async def delete_data(self, table_name: str, where: str, schema_name: str = None) -> Dict[str, Any]:
        try:
            if not await self.connect():
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            schema_name = schema_name or "public"
            query = f'DELETE FROM "{schema_name}"."{table_name}" WHERE {where}'
            result = await self.conn.execute(query)
            affected_rows = int(result.split()[-1]) if result and result.split()[-1].isdigit() else 0
            return {"success": True, "message": f"删除成功，影响 {affected_rows} 行", "affected_rows": affected_rows}
        except Exception as e:
            return {"success": False, "message": str(e), "affected_rows": 0}
        finally:
            await self.close()

    async def execute_ddl(self, sql: str, database: str = None, schema_name: str = None) -> Dict[str, Any]:
        try:
            if not await self.connect(database):
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            if schema_name:
                await self.conn.execute(f"SET search_path TO {schema_name}, public")
            await self.conn.execute(sql)
            return {"success": True, "message": "DDL执行成功", "affected_rows": 0}
        except Exception as e:
            return {"success": False, "message": f"DDL执行失败: {str(e)}", "affected_rows": 0}
        finally:
            await self.close()


# ============ MySQL Handler ============
class MySQLHandler:
    """MySQL异步处理器"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None

    async def connect(self, database: str = None) -> bool:
        try:
            # 如果已有连接，先关闭
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None
            
            import aiomysql
            self.conn = await aiomysql.connect(
                host=self.host, port=self.port, user=self.user,
                password=self.password, db=database or self.database,
                charset='utf8mb4', connect_timeout=10, autocommit=True,
                read_timeout=60,  # 读取超时
                write_timeout=60,  # 写入超时
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            self.conn = None
            return False

    async def close(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                logger.warning(f"Error closing MySQL connection: {e}")
            finally:
                self.conn = None

    async def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        import aiomysql
        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def _execute_command(self, command: str, params: tuple = None) -> int:
        async with self.conn.cursor() as cursor:
            await cursor.execute(command, params or ())
            return cursor.rowcount

    async def get_databases(self) -> List[Dict[str, Any]]:
        try:
            if not await self.connect():
                return []
            query = """
                SELECT SCHEMA_NAME as name, DEFAULT_CHARACTER_SET_NAME as encoding, DEFAULT_COLLATION_NAME as collation,
                       (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = SCHEMA_NAME AND TABLE_TYPE = 'BASE TABLE') as tables_count
                FROM information_schema.SCHEMATA
                WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys') ORDER BY SCHEMA_NAME
            """
            databases = await self._execute_query(query)
            for db in databases:
                size_result = await self._execute_query("SELECT ROUND(SUM(data_length + index_length), 2) as size_bytes FROM information_schema.TABLES WHERE table_schema = %s", (db['name'],))
                size_bytes = size_result[0]['size_bytes'] if size_result and size_result[0]['size_bytes'] else 0
                db['size_bytes'] = int(size_bytes) if size_bytes else 0
                db['size'] = format_size(db['size_bytes'])
            return databases
        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []
        finally:
            await self.close()

    async def create_database(self, name: str, charset: str = "utf8mb4", collation: str = "utf8mb4_unicode_ci", **kwargs) -> bool:
        try:
            if not await self.connect():
                return False
            await self._execute_command(f"CREATE DATABASE `{name}` CHARACTER SET {charset} COLLATE {collation}")
            return True
        except Exception as e:
            logger.error(f"Failed to create database {name}: {e}")
            raise
        finally:
            await self.close()

    async def drop_database(self, name: str) -> bool:
        try:
            if not await self.connect():
                return False
            await self._execute_command(f"DROP DATABASE `{name}`")
            return True
        except Exception as e:
            logger.error(f"Failed to drop database {name}: {e}")
            raise
        finally:
            await self.close()

    async def get_schemas(self, database: str = None) -> List[Dict[str, Any]]:
        databases = await self.get_databases()
        return [{"name": db["name"], "owner": None, "tables_count": db.get("tables_count", 0)} for db in databases]

    async def get_tables(self, database: str = None, schema_name: str = None) -> List[Dict[str, Any]]:
        try:
            db_name = database or schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT TABLE_SCHEMA as schema_name, TABLE_NAME as table_name, TABLE_TYPE as table_type,
                       TABLE_ROWS as row_count, DATA_LENGTH as data_length, INDEX_LENGTH as index_length,
                       (DATA_LENGTH + INDEX_LENGTH) as total_size_bytes, TABLE_COMMENT as description
                FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME
            """
            tables = await self._execute_query(query, (db_name,))
            for table in tables:
                table['total_size'] = format_size(table.get('total_size_bytes', 0) or 0)
            return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []
        finally:
            await self.close()

    async def get_table_columns(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type, IS_NULLABLE = 'YES' as is_nullable,
                       COLUMN_DEFAULT as column_default, CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
                       NUMERIC_PRECISION as numeric_precision, NUMERIC_SCALE as numeric_scale,
                       ORDINAL_POSITION as ordinal_position, COLUMN_KEY = 'PRI' as is_primary_key,
                       COLUMN_KEY = 'UNI' as is_unique, COLUMN_COMMENT as description
                FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION
            """
            rows = await self._execute_query(query, (db_name, table_name))
            return rows
        except Exception as e:
            logger.error(f"Failed to get table columns: {e}")
            return []
        finally:
            await self.close()

    async def get_table_indexes(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT INDEX_NAME as index_name, INDEX_TYPE as index_type,
                       GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                       NON_UNIQUE = 0 as is_unique, INDEX_NAME = 'PRIMARY' as is_primary
                FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                GROUP BY INDEX_NAME, INDEX_TYPE, NON_UNIQUE ORDER BY INDEX_NAME
            """
            indexes = await self._execute_query(query, (db_name, table_name))
            for idx in indexes:
                idx['definition'] = f"INDEX {idx['index_name']} ({idx['columns']})"
            return indexes
        except Exception as e:
            logger.error(f"Failed to get table indexes: {e}")
            return []
        finally:
            await self.close()

    async def get_table_constraints(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT tc.CONSTRAINT_NAME as constraint_name, tc.CONSTRAINT_TYPE as constraint_type,
                       GROUP_CONCAT(kcu.COLUMN_NAME) as columns, kcu.REFERENCED_TABLE_NAME as referenced_table, NULL as referenced_columns
                FROM information_schema.TABLE_CONSTRAINTS tc
                JOIN information_schema.KEY_COLUMN_USAGE kcu ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA AND tc.TABLE_NAME = kcu.TABLE_NAME
                WHERE tc.TABLE_SCHEMA = %s AND tc.TABLE_NAME = %s
                GROUP BY tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE, kcu.REFERENCED_TABLE_NAME ORDER BY tc.CONSTRAINT_TYPE, tc.CONSTRAINT_NAME
            """
            constraints = await self._execute_query(query, (db_name, table_name))
            for const in constraints:
                const['definition'] = f"{const['constraint_type']} ({const['columns']})"
            return constraints
        except Exception as e:
            logger.error(f"Failed to get table constraints: {e}")
            return []
        finally:
            await self.close()

    async def get_table_structure(self, table_name: str, database: str = None, schema_name: str = None) -> Dict[str, Any]:
        db_name = database or schema_name or self.database
        tables = await self.get_tables(database=db_name, schema_name=db_name)
        table_info = next((t for t in tables if t['table_name'] == table_name), None)
        if not table_info:
            raise ValueError(f"Table {db_name}.{table_name} not found")
        columns = await self.get_table_columns(table_name, db_name)
        indexes = await self.get_table_indexes(table_name, db_name)
        constraints = await self.get_table_constraints(table_name, db_name)
        return {"table_info": table_info, "columns": columns, "indexes": indexes, "constraints": constraints}

    async def get_table_ddl(self, table_name: str, schema_name: str = None) -> str:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return "-- 无法连接数据库"
            result = await self._execute_query(f"SHOW CREATE TABLE `{table_name}`")
            if result:
                return result[0].get('Create Table', f"-- 无法获取表 {table_name} 的DDL")
            return f"-- 无法获取表 {table_name} 的DDL"
        except Exception as e:
            return f"-- 获取DDL失败: {str(e)}"
        finally:
            await self.close()

    async def get_views(self, database: str = None, schema_name: str = None) -> List[Dict[str, Any]]:
        try:
            db_name = database or schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT TABLE_NAME as view_name, TABLE_SCHEMA as schema_name, VIEW_DEFINITION as view_definition,
                       IS_UPDATABLE as is_updatable, CHECK_OPTION as check_option, 'VIEW' as view_type
                FROM information_schema.VIEWS WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME
            """
            result = await self._execute_query(query, (db_name,))
            for row in result:
                row['is_updatable'] = row.get('is_updatable') == 'YES'
            return result
        except Exception as e:
            logger.error(f"Failed to get views: {e}")
            return []
        finally:
            await self.close()

    async def get_view_structure(self, view_name: str, schema_name: str = None) -> Dict[str, Any]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                raise ValueError("Failed to connect")
            view_query = "SELECT TABLE_NAME as view_name, TABLE_SCHEMA as schema_name, VIEW_DEFINITION as view_definition, IS_UPDATABLE as is_updatable, CHECK_OPTION as check_option, 'VIEW' as view_type FROM information_schema.VIEWS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
            view_info = await self._execute_query(view_query, (db_name, view_name))
            if not view_info:
                raise ValueError(f"View {db_name}.{view_name} not found")
            view_info = view_info[0]
            view_info['is_updatable'] = view_info.get('is_updatable') == 'YES'
            columns_query = "SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type, IS_NULLABLE = 'YES' as is_nullable, ORDINAL_POSITION as ordinal_position, COLUMN_COMMENT as description FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION"
            columns = await self._execute_query(columns_query, (db_name, view_name))
            definition_sql = await self._get_view_definition_internal(view_name)
            dependencies = await self._get_view_dependencies_internal(view_name, db_name)
            return {"view_info": view_info, "columns": columns, "dependencies": dependencies, "definition_sql": definition_sql}
        except Exception as e:
            logger.error(f"Failed to get view structure: {e}")
            raise
        finally:
            await self.close()

    async def _get_view_definition_internal(self, view_name: str) -> str:
        try:
            result = await self._execute_query(f"SHOW CREATE VIEW `{view_name}`")
            if result:
                return result[0].get('Create View', f"-- 无法获取视图 {view_name} 的定义")
        except Exception as e:
            logger.error(f"Failed to get view definition: {e}")
        return f"-- 无法获取视图 {view_name} 的定义"

    async def _get_view_dependencies_internal(self, view_name: str, schema_name: str) -> List[str]:
        try:
            query = "SELECT DISTINCT REFERENCED_TABLE_NAME as table_name FROM information_schema.VIEW_TABLE_USAGE WHERE VIEW_SCHEMA = %s AND VIEW_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY REFERENCED_TABLE_NAME"
            result = await self._execute_query(query, (schema_name, view_name))
            return [row['table_name'] for row in result]
        except Exception as e:
            logger.error(f"Failed to get view dependencies: {e}")
            return []

    async def get_view_definition(self, view_name: str, schema_name: str = None) -> str:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return "-- 无法连接数据库"
            result = await self._get_view_definition_internal(view_name)
            return result
        except Exception as e:
            return f"-- 获取视图定义失败: {str(e)}"
        finally:
            await self.close()

    async def get_view_dependencies(self, view_name: str, schema_name: str = None) -> List[str]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            result = await self._get_view_dependencies_internal(view_name, db_name)
            return result
        except Exception as e:
            return []
        finally:
            await self.close()

    async def query_data(self, table_name: str, schema_name: str = None, page: int = 1, page_size: int = 20, where: str = None, order_by: str = None) -> Dict[str, Any]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"columns": [], "rows": [], "total": 0, "page": page, "page_size": page_size}
            count_q = f"SELECT COUNT(*) as total FROM `{table_name}`" + (f" WHERE {where}" if where else "")
            count_result = await self._execute_query(count_q)
            total = count_result[0]['total'] if count_result else 0
            offset = (page - 1) * page_size
            data_q = f"SELECT * FROM `{table_name}`" + (f" WHERE {where}" if where else "") + (f" ORDER BY {order_by}" if order_by else "") + f" LIMIT {page_size} OFFSET {offset}"
            rows = await self._execute_query(data_q)
            rows_list = [serialize_row(row) for row in rows]
            columns = list(rows_list[0].keys()) if rows_list else []
            return {"columns": columns, "rows": rows_list, "total": total, "page": page, "page_size": page_size}
        except Exception as e:
            logger.error(f"Failed to query data: {e}")
            return {"columns": [], "rows": [], "total": 0, "page": page, "page_size": page_size}
        finally:
            await self.close()

    async def execute_sql(self, sql: str, is_query: bool = True) -> Dict[str, Any]:
        start_time = time.time()
        try:
            if not await self.connect():
                return {"success": False, "message": "数据库连接失败", "columns": None, "rows": None, "affected_rows": None, "execution_time": 0}
            if is_query:
                rows = await self._execute_query(sql)
                execution_time = time.time() - start_time
                rows_list = [serialize_row(row) for row in rows]
                columns = list(rows_list[0].keys()) if rows_list else []
                return {"success": True, "message": f"查询成功，返回 {len(rows_list)} 行", "columns": columns, "rows": rows_list, "affected_rows": None, "execution_time": round(execution_time, 3)}
            else:
                affected_rows = await self._execute_command(sql)
                execution_time = time.time() - start_time
                return {"success": True, "message": f"执行成功，影响 {affected_rows} 行", "columns": None, "rows": None, "affected_rows": affected_rows, "execution_time": round(execution_time, 3)}
        except Exception as e:
            return {"success": False, "message": str(e), "columns": None, "rows": None, "affected_rows": None, "execution_time": round(time.time() - start_time, 3)}
        finally:
            await self.close()

    async def insert_data(self, table_name: str, data: Dict[str, Any], schema_name: str = None) -> Dict[str, Any]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ', '.join(['%s'] * len(values))
            query = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({placeholders})"
            affected_rows = await self._execute_command(query, tuple(values))
            return {"success": True, "message": "插入成功", "affected_rows": affected_rows}
        except Exception as e:
            return {"success": False, "message": str(e), "affected_rows": 0}
        finally:
            await self.close()

    async def update_data(self, table_name: str, data: Dict[str, Any], where: str, schema_name: str = None) -> Dict[str, Any]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            set_clause = ', '.join([f'{k} = %s' for k in data.keys()])
            query = f"UPDATE `{table_name}` SET {set_clause} WHERE {where}"
            affected_rows = await self._execute_command(query, tuple(data.values()))
            return {"success": True, "message": f"更新成功，影响 {affected_rows} 行", "affected_rows": affected_rows}
        except Exception as e:
            return {"success": False, "message": str(e), "affected_rows": 0}
        finally:
            await self.close()

    async def delete_data(self, table_name: str, where: str, schema_name: str = None) -> Dict[str, Any]:
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            query = f"DELETE FROM `{table_name}` WHERE {where}"
            affected_rows = await self._execute_command(query)
            return {"success": True, "message": f"删除成功，影响 {affected_rows} 行", "affected_rows": affected_rows}
        except Exception as e:
            return {"success": False, "message": str(e), "affected_rows": 0}
        finally:
            await self.close()

    async def execute_ddl(self, sql: str, database: str = None, schema_name: str = None) -> Dict[str, Any]:
        try:
            db_name = database or schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "数据库连接失败", "affected_rows": 0}
            await self._execute_command(sql)
            return {"success": True, "message": "DDL执行成功", "affected_rows": 0}
        except Exception as e:
            return {"success": False, "message": f"DDL执行失败: {str(e)}", "affected_rows": 0}
        finally:
            await self.close()


# ============ 统一服务类 ============
class AsyncDatabaseManagerService:
    """异步数据库管理服务（工厂类）"""

    def __init__(self, db_name: str = "default"):
        self.db_name = db_name
        db_info = parse_database_url(settings.DATABASE_URL)
        if not db_info:
            raise ValueError("Invalid DATABASE_URL")

        self.db_type = db_info['db_type']
        self.host = db_info['host']
        self.port = db_info['port']
        self.user = db_info['user']
        self.password = db_info['password']
        self.database = db_info['database']

        if self.db_type == 'postgresql':
            self._handler = PostgreSQLHandler(self.host, self.port, self.user, self.password, self.database)
        elif self.db_type == 'mysql':
            self._handler = MySQLHandler(self.host, self.port, self.user, self.password, self.database)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    @staticmethod
    def get_database_configs() -> List[Dict[str, Any]]:
        configs = []
        db_info = parse_database_url(settings.DATABASE_URL)
        if db_info:
            configs.append({
                'db_name': 'default', 'name': db_info['database'], 'db_type': db_info['db_type'],
                'host': db_info['host'], 'port': db_info['port'], 'database': db_info['database'],
                'user': db_info['user'], 'has_password': bool(db_info['password'])
            })
        return configs

    async def test_connection(self) -> Dict[str, Any]:
        try:
            if await self._handler.connect():
                return {"success": True, "message": "数据库连接成功", "db_name": self.db_name, "db_type": self.db_type}
            return {"success": False, "message": "数据库连接失败", "db_name": self.db_name}
        except Exception as e:
            return {"success": False, "message": f"数据库连接失败: {str(e)}", "db_name": self.db_name}
        finally:
            await self._handler.close()

    # 代理所有方法到handler
    async def get_databases(self) -> List[Dict[str, Any]]:
        return await self._handler.get_databases()

    async def create_database(self, name: str, **kwargs) -> bool:
        return await self._handler.create_database(name, **kwargs)

    async def drop_database(self, name: str) -> bool:
        return await self._handler.drop_database(name)

    async def get_schemas(self, database: str = None) -> List[Dict[str, Any]]:
        return await self._handler.get_schemas(database)

    async def get_tables(self, database: str = None, schema_name: str = None) -> List[Dict[str, Any]]:
        return await self._handler.get_tables(database, schema_name or "public")

    async def get_table_columns(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        return await self._handler.get_table_columns(table_name, schema_name)

    async def get_table_indexes(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        return await self._handler.get_table_indexes(table_name, schema_name)

    async def get_table_constraints(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        return await self._handler.get_table_constraints(table_name, schema_name)

    async def get_table_structure(self, table_name: str, database: str = None, schema_name: str = None) -> Dict[str, Any]:
        return await self._handler.get_table_structure(table_name, database, schema_name)

    async def get_table_ddl(self, table_name: str, schema_name: str = None) -> str:
        return await self._handler.get_table_ddl(table_name, schema_name)

    async def get_views(self, database: str = None, schema_name: str = None) -> List[Dict[str, Any]]:
        return await self._handler.get_views(database, schema_name)

    async def get_view_structure(self, view_name: str, schema_name: str = None) -> Dict[str, Any]:
        return await self._handler.get_view_structure(view_name, schema_name)

    async def get_view_definition(self, view_name: str, schema_name: str = None) -> str:
        return await self._handler.get_view_definition(view_name, schema_name)

    async def get_view_dependencies(self, view_name: str, schema_name: str = None) -> List[str]:
        return await self._handler.get_view_dependencies(view_name, schema_name)

    async def query_data(self, table_name: str, schema_name: str = None, page: int = 1, page_size: int = 20, where: str = None, order_by: str = None) -> Dict[str, Any]:
        return await self._handler.query_data(table_name, schema_name, page, page_size, where, order_by)

    async def execute_sql(self, sql: str, is_query: bool = True) -> Dict[str, Any]:
        return await self._handler.execute_sql(sql, is_query)

    async def insert_data(self, table_name: str, data: Dict[str, Any], schema_name: str = None) -> Dict[str, Any]:
        return await self._handler.insert_data(table_name, data, schema_name)

    async def update_data(self, table_name: str, data: Dict[str, Any], where: str, schema_name: str = None) -> Dict[str, Any]:
        return await self._handler.update_data(table_name, data, where, schema_name)

    async def delete_data(self, table_name: str, where: str, schema_name: str = None) -> Dict[str, Any]:
        return await self._handler.delete_data(table_name, where, schema_name)

    async def execute_ddl(self, sql: str, database: str = None, schema_name: str = None) -> Dict[str, Any]:
        return await self._handler.execute_ddl(sql, database, schema_name)