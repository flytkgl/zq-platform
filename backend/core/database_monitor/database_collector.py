#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库信息收集器（异步版本）
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any

import asyncpg

logger = logging.getLogger(__name__)

# MySQL异步驱动
try:
    import aiomysql
    AIOMYSQL_AVAILABLE = True
except ImportError:
    AIOMYSQL_AVAILABLE = False


def serialize_data(data: Any) -> Any:
    """递归地序列化数据，处理datetime、decimal等类型"""
    import decimal

    if isinstance(data, (datetime,)):
        return data.isoformat()
    elif isinstance(data, decimal.Decimal):
        return float(data)
    elif isinstance(data, (bytes,)):
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return str(data)
    elif isinstance(data, dict):
        return {serialize_data(k): serialize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(serialize_data(item) for item in data)
    else:
        return data


class AsyncDatabaseCollector:
    """异步数据库信息收集器"""

    def __init__(self, db_type: str, host: str, port: int,
                 user: str, password: str, database: str, **kwargs):
        self.db_type = db_type.upper()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.kwargs = kwargs
        self.connection = None

    async def connect(self) -> bool:
        """连接数据库"""
        try:
            if self.db_type == 'POSTGRESQL':
                return await self._connect_postgresql()
            elif self.db_type == 'MYSQL':
                return await self._connect_mysql()
            else:
                logger.error(f"Unsupported database type: {self.db_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.db_type} database: {e}")
            return False

    async def _connect_postgresql(self) -> bool:
        """连接PostgreSQL"""
        self.connection = await asyncpg.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            timeout=5
        )
        return True

    async def _connect_mysql(self) -> bool:
        """连接MySQL"""
        if not AIOMYSQL_AVAILABLE:
            logger.error("aiomysql not available")
            return False

        self.connection = await aiomysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            charset='utf8mb4',
            connect_timeout=5
        )
        return True

    async def disconnect(self):
        """断开连接"""
        if self.connection:
            try:
                await self.connection.close()
            except Exception as e:
                logger.error(f"Error disconnecting from database: {e}")
            finally:
                self.connection = None

    async def test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        start_time = time.time()
        try:
            if await self.connect():
                response_time = (time.time() - start_time) * 1000
                version = await self._get_version()
                return {
                    'success': True,
                    'message': '连接成功',
                    'response_time': round(response_time, 2),
                    'version': version,
                    'db_type': self.db_type
                }
            else:
                return {
                    'success': False,
                    'message': '连接失败',
                    'response_time': None,
                    'version': None,
                    'db_type': self.db_type
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'连接错误: {str(e)}',
                'response_time': None,
                'version': None,
                'db_type': self.db_type
            }
        finally:
            await self.disconnect()

    async def _get_version(self) -> str:
        """获取数据库版本"""
        try:
            if self.db_type == 'POSTGRESQL':
                result = await self.connection.fetchval("SELECT version()")
                return result
            elif self.db_type == 'MYSQL':
                async with self.connection.cursor() as cursor:
                    await cursor.execute("SELECT VERSION()")
                    result = await cursor.fetchone()
                    return result[0]
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error getting database version: {e}")
            return 'Unknown'

    async def get_basic_info(self) -> Dict[str, Any]:
        """获取数据库基本信息"""
        if not self.connection:
            if not await self.connect():
                return {}

        try:
            info = {
                'db_type': self.db_type,
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'version': await self._get_version(),
                'uptime': await self._get_uptime(),
                'timezone': await self._get_timezone(),
                'charset': await self._get_charset(),
            }
            return serialize_data(info)
        except Exception as e:
            logger.error(f"Error getting basic info: {e}")
            return {}

    async def _get_uptime(self) -> str:
        """获取数据库运行时间"""
        try:
            if self.db_type == 'POSTGRESQL':
                start_time = await self.connection.fetchval("SELECT pg_postmaster_start_time()")
                current_time = datetime.now(timezone.utc)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                uptime = current_time - start_time
                return str(uptime)
            elif self.db_type == 'MYSQL':
                async with self.connection.cursor() as cursor:
                    await cursor.execute("SHOW GLOBAL STATUS LIKE 'Uptime'")
                    result = await cursor.fetchone()
                    if result:
                        uptime_seconds = int(result[1])
                        uptime = timedelta(seconds=uptime_seconds)
                        return str(uptime)
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return 'Unknown'

    async def _get_timezone(self) -> str:
        """获取数据库时区"""
        try:
            if self.db_type == 'POSTGRESQL':
                result = await self.connection.fetchval("SHOW timezone")
                return result
            elif self.db_type == 'MYSQL':
                async with self.connection.cursor() as cursor:
                    await cursor.execute("SELECT @@global.time_zone")
                    result = await cursor.fetchone()
                    return result[0]
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error getting timezone: {e}")
            return 'Unknown'

    async def _get_charset(self) -> str:
        """获取数据库字符集"""
        try:
            if self.db_type == 'POSTGRESQL':
                result = await self.connection.fetchval(
                    "SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = $1",
                    self.database
                )
                return result
            elif self.db_type == 'MYSQL':
                async with self.connection.cursor() as cursor:
                    await cursor.execute("SELECT @@character_set_database")
                    result = await cursor.fetchone()
                    return result[0]
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error getting charset: {e}")
            return 'Unknown'

    async def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        if not self.connection:
            if not await self.connect():
                return {}

        try:
            if self.db_type == 'POSTGRESQL':
                return await self._get_postgresql_connections()
            elif self.db_type == 'MYSQL':
                return await self._get_mysql_connections()
            return {}
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            return {}

    async def _get_postgresql_connections(self) -> Dict[str, Any]:
        """获取PostgreSQL连接信息"""
        total_connections = await self.connection.fetchval(
            "SELECT COUNT(*) FROM pg_stat_activity"
        )
        
        max_connections = await self.connection.fetchval("SHOW max_connections")
        max_connections = int(max_connections)
        
        active_connections = await self.connection.fetchval(
            "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'"
        )
        
        idle_connections = await self.connection.fetchval(
            "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'idle'"
        )

        return {
            'total_connections': total_connections,
            'max_connections': max_connections,
            'active_connections': active_connections,
            'idle_connections': idle_connections,
            'connection_usage_percent': round((total_connections / max_connections) * 100, 2) if max_connections > 0 else 0.0
        }

    async def _get_mysql_connections(self) -> Dict[str, Any]:
        """获取MySQL连接信息"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            result = await cursor.fetchone()
            total_connections = int(result[1])

            await cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
            result = await cursor.fetchone()
            max_connections = int(result[1])

            await cursor.execute("SHOW STATUS LIKE 'Threads_running'")
            result = await cursor.fetchone()
            active_connections = int(result[1])

        idle_connections = total_connections - active_connections

        return {
            'total_connections': total_connections,
            'max_connections': max_connections,
            'active_connections': active_connections,
            'idle_connections': idle_connections,
            'connection_usage_percent': round((total_connections / max_connections) * 100, 2) if max_connections > 0 else 0.0
        }

    async def get_database_size(self) -> Dict[str, Any]:
        """获取数据库大小信息"""
        if not self.connection:
            if not await self.connect():
                return {}

        try:
            if self.db_type == 'POSTGRESQL':
                return await self._get_postgresql_size()
            elif self.db_type == 'MYSQL':
                return await self._get_mysql_size()
            return {}
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return {}

    async def _get_postgresql_size(self) -> Dict[str, Any]:
        """获取PostgreSQL数据库大小"""
        size_bytes = await self.connection.fetchval(
            "SELECT pg_database_size($1)", self.database
        )

        return {
            'database_size_bytes': size_bytes,
            'database_size_mb': round(size_bytes / 1024 / 1024, 2),
            'database_size_gb': round(size_bytes / 1024 / 1024 / 1024, 2)
        }

    async def _get_mysql_size(self) -> Dict[str, Any]:
        """获取MySQL数据库大小"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT SUM(data_length + index_length) AS size_bytes
                FROM information_schema.tables
                WHERE table_schema = %s
            """, (self.database,))
            result = await cursor.fetchone()
            size_bytes = result[0] if result[0] else 0

        return {
            'database_size_bytes': size_bytes,
            'database_size_mb': round(size_bytes / 1024 / 1024, 2),
            'database_size_gb': round(size_bytes / 1024 / 1024 / 1024, 2)
        }

    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        if not self.connection:
            if not await self.connect():
                return {'cache_hit_ratio': 0.0}

        try:
            if self.db_type == 'POSTGRESQL':
                return await self._get_postgresql_performance()
            elif self.db_type == 'MYSQL':
                return await self._get_mysql_performance()
            return {'cache_hit_ratio': 0.0}
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {'cache_hit_ratio': 0.0}

    async def _get_postgresql_performance(self) -> Dict[str, Any]:
        """获取PostgreSQL性能统计"""
        stats = await self.connection.fetchrow("""
            SELECT SUM(numbackends) AS total_backends,
                   SUM(xact_commit) AS transactions_commit,
                   SUM(xact_rollback) AS transactions_rollback,
                   SUM(blks_read) AS blocks_read,
                   SUM(blks_hit) AS blocks_hit,
                   SUM(tup_returned) AS tuples_returned,
                   SUM(tup_fetched) AS tuples_fetched,
                   SUM(tup_inserted) AS tuples_inserted,
                   SUM(tup_updated) AS tuples_updated,
                   SUM(tup_deleted) AS tuples_deleted,
                   SUM(temp_files) AS temp_files,
                   SUM(temp_bytes) AS temp_bytes,
                   SUM(deadlocks) AS deadlocks
            FROM pg_stat_database
            WHERE datname = $1
        """, self.database)

        blocks_read = stats['blocks_read'] or 0
        blocks_hit = stats['blocks_hit'] or 0
        total_reads = blocks_read + blocks_hit
        cache_hit_ratio = (blocks_hit / total_reads * 100) if total_reads > 0 else 0

        return {
            'total_backends': stats['total_backends'] or 0,
            'transactions_commit': stats['transactions_commit'] or 0,
            'transactions_rollback': stats['transactions_rollback'] or 0,
            'blocks_read': blocks_read,
            'blocks_hit': blocks_hit,
            'cache_hit_ratio': round(cache_hit_ratio, 2),
            'tuples_returned': stats['tuples_returned'] or 0,
            'tuples_fetched': stats['tuples_fetched'] or 0,
            'tuples_inserted': stats['tuples_inserted'] or 0,
            'tuples_updated': stats['tuples_updated'] or 0,
            'tuples_deleted': stats['tuples_deleted'] or 0,
            'temp_files': stats['temp_files'] or 0,
            'temp_bytes': stats['temp_bytes'] or 0,
            'deadlocks': stats['deadlocks'] or 0,
        }

    async def _get_mysql_performance(self) -> Dict[str, Any]:
        """获取MySQL性能统计"""
        stats = {}
        status_queries = [
            ('queries', 'Queries'),
            ('connections', 'Connections'),
            ('slow_queries', 'Slow_queries'),
            ('bytes_received', 'Bytes_received'),
            ('bytes_sent', 'Bytes_sent'),
            ('innodb_buffer_pool_reads', 'Innodb_buffer_pool_reads'),
            ('innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_read_requests')
        ]

        async with self.connection.cursor() as cursor:
            for stat_name, mysql_var in status_queries:
                await cursor.execute(f"SHOW GLOBAL STATUS LIKE '{mysql_var}'")
                result = await cursor.fetchone()
                stats[stat_name] = int(result[1]) if result else 0

        read_requests = stats['innodb_buffer_pool_read_requests']
        reads = stats['innodb_buffer_pool_reads']
        cache_hit_ratio = ((read_requests - reads) / read_requests * 100) if read_requests > 0 else 0

        return {
            'total_queries': stats['queries'],
            'total_connections': stats['connections'],
            'slow_queries': stats['slow_queries'],
            'bytes_received': stats['bytes_received'],
            'bytes_sent': stats['bytes_sent'],
            'cache_hit_ratio': round(cache_hit_ratio, 2)
        }

    async def get_table_stats(self) -> List[Dict[str, Any]]:
        """获取表统计信息"""
        if not self.connection:
            if not await self.connect():
                return []

        try:
            if self.db_type == 'POSTGRESQL':
                return await self._get_postgresql_tables()
            elif self.db_type == 'MYSQL':
                return await self._get_mysql_tables()
            return []
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return []

    async def _get_postgresql_tables(self) -> List[Dict[str, Any]]:
        """获取PostgreSQL表统计"""
        rows = await self.connection.fetch("""
            SELECT st.schemaname,
                   st.relname AS tablename,
                   st.n_tup_ins AS inserts,
                   st.n_tup_upd AS updates,
                   st.n_tup_del AS deletes,
                   st.n_live_tup AS live_tuples,
                   st.n_dead_tup AS dead_tuples,
                   st.seq_scan AS sequential_scans,
                   st.idx_scan AS index_scans,
                   COALESCE(PG_SIZE_PRETTY(PG_RELATION_SIZE(c.oid)), '0 bytes') AS size,
                   COALESCE(PG_RELATION_SIZE(c.oid), 0) AS size_bytes,
                   COALESCE(PG_SIZE_PRETTY(PG_TOTAL_RELATION_SIZE(c.oid)), '0 bytes') AS total_size,
                   COALESCE(PG_TOTAL_RELATION_SIZE(c.oid), 0) AS total_size_bytes
            FROM pg_stat_user_tables st
            JOIN pg_class c ON c.relname = st.relname 
                AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = st.schemaname)
            WHERE c.relkind = 'r'
            ORDER BY COALESCE(PG_TOTAL_RELATION_SIZE(c.oid), 0) DESC
            LIMIT 20
        """)

        return [dict(row) for row in rows]

    async def _get_mysql_tables(self) -> List[Dict[str, Any]]:
        """获取MySQL表统计"""
        async with self.connection.cursor() as cursor:
            await cursor.execute("""
                SELECT table_name,
                       table_rows,
                       data_length,
                       index_length,
                       (data_length + index_length) AS total_size,
                       auto_increment
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY (data_length + index_length) DESC
                LIMIT 20
            """, (self.database,))

            tables = []
            rows = await cursor.fetchall()
            for row in rows:
                tables.append({
                    'table_name': row[0],
                    'table_rows': row[1] or 0,
                    'data_length': row[2] or 0,
                    'index_length': row[3] or 0,
                    'total_size': row[4] or 0,
                    'auto_increment': row[5] or 0
                })
        return tables

    async def get_all_info(self, connection_id: str, connection_name: str) -> Dict[str, Any]:
        """获取所有数据库监控信息"""
        timestamp = datetime.now().isoformat()

        try:
            if not await self.connect():
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'disconnected',
                    'basic_info': {},
                    'connection_info': {},
                    'database_size': {},
                    'performance_stats': {'cache_hit_ratio': 0.0},
                    'table_stats': [],
                    'timestamp': timestamp
                }

            data = {
                'connection_id': connection_id,
                'connection_name': connection_name,
                'status': 'connected',
                'basic_info': await self.get_basic_info(),
                'connection_info': await self.get_connection_info(),
                'database_size': await self.get_database_size(),
                'performance_stats': await self.get_performance_stats(),
                'table_stats': await self.get_table_stats(),
                'timestamp': timestamp
            }
            return serialize_data(data)
        except Exception as e:
            logger.error(f"Error getting database all info: {e}")
            return {
                'connection_id': connection_id,
                'connection_name': connection_name,
                'status': 'error',
                'basic_info': {},
                'connection_info': {},
                'database_size': {},
                'performance_stats': {'cache_hit_ratio': 0.0},
                'table_stats': [],
                'timestamp': timestamp
            }
        finally:
            await self.disconnect()

    async def get_realtime_stats(self, connection_id: str) -> Dict[str, Any]:
        """获取实时统计信息"""
        timestamp = datetime.now().isoformat()

        try:
            if not await self.connect():
                return {
                    'connection_id': connection_id,
                    'connections_used': 0,
                    'connection_usage_percent': 0.0,
                    'database_size_mb': 0.0,
                    'cache_hit_ratio': 0.0,
                    'active_connections': 0,
                    'timestamp': timestamp
                }

            connection_info = await self.get_connection_info()
            database_size = await self.get_database_size()
            performance_stats = await self.get_performance_stats()

            data = {
                'connection_id': connection_id,
                'connections_used': connection_info.get('total_connections', 0),
                'connection_usage_percent': connection_info.get('connection_usage_percent', 0.0),
                'database_size_mb': database_size.get('database_size_mb', 0.0),
                'cache_hit_ratio': performance_stats.get('cache_hit_ratio', 0.0),
                'active_connections': connection_info.get('active_connections', 0),
                'timestamp': timestamp
            }
            return serialize_data(data)
        except Exception as e:
            logger.error(f"Error getting database realtime stats: {e}")
            return {
                'connection_id': connection_id,
                'connections_used': 0,
                'connection_usage_percent': 0.0,
                'database_size_mb': 0.0,
                'cache_hit_ratio': 0.0,
                'active_connections': 0,
                'timestamp': timestamp
            }
        finally:
            await self.disconnect()
