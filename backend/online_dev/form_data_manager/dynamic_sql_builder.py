#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态 SQL 构建器（异步版本）
支持 PostgreSQL、MySQL 的 SQL 语法差异
"""
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from app.timezone import APP_TIMEZONE


class DynamicSQLBuilder:
    """动态 SQL 构建器 - 适配多种数据库"""

    def __init__(self, db_type: str):
        """
        初始化 SQL 构建器
        
        Args:
            db_type: 数据库类型 (postgresql, mysql)
        """
        self.db_type = db_type.lower()

    # ============ 标识符引用 ============

    def quote_identifier(self, name: str) -> str:
        """
        引用标识符（表名、列名等）
        
        PostgreSQL: "name"
        MySQL: `name`
        """
        if self.db_type == "postgresql":
            return f'"{name}"'
        elif self.db_type == "mysql":
            return f"`{name}`"
        return name

    def build_table_name(self, table: str, schema: Optional[str] = None,
                         database: Optional[str] = None) -> str:
        """
        构建完整的表名
        
        PostgreSQL: schema.table 或 table
        MySQL: database.table 或 table
        """
        parts = []

        if self.db_type == "postgresql":
            if schema:
                parts.append(self.quote_identifier(schema))
        elif self.db_type == "mysql":
            if database:
                parts.append(self.quote_identifier(database))

        parts.append(self.quote_identifier(table))
        return ".".join(parts)

    # ============ 参数占位符 ============

    def get_placeholder(self, index: int = 0) -> str:
        """
        获取参数占位符
        
        PostgreSQL: $1, $2, ...
        MySQL: %s
        """
        if self.db_type == "postgresql":
            return f"${index + 1}"
        return "%s"

    def get_placeholders(self, count: int, start_index: int = 0) -> List[str]:
        """获取多个占位符"""
        return [self.get_placeholder(start_index + i) for i in range(count)]

    # ============ 数据类型转换 ============

    @staticmethod
    def _convert_value(value: Any) -> Any:
        """
        转换数据值为适合数据库的类型
        
        注意：日期时间的转换应该由 service.py 的 _convert_data_types 方法
        根据字段类型来处理，这里只处理基本的数据结构转换
        
        Args:
            value: 原始值
            
        Returns:
            转换后的值
        """
        # 处理列表和字典类型
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        
        return value

    def _build_like_expr(self, quoted_field: str, case_sensitive: bool) -> str:
        """根据数据库类型和大小写敏感标志构建 LIKE 表达式
        
        Args:
            quoted_field: 已引用的字段名
            case_sensitive: True=大小写敏感, False=大小写不敏感
        
        Returns:
            如: "CAST(name AS TEXT) LIKE :p" 或 "CAST(name AS TEXT) ILIKE :p"
        """
        if self.db_type == "postgresql":
            if case_sensitive:
                return f"CAST({quoted_field} AS TEXT) LIKE :{{}}"
            else:
                return f"CAST({quoted_field} AS TEXT) ILIKE :{{}}"
        else:
            if case_sensitive:
                return f"CAST({quoted_field} AS CHAR) LIKE BINARY :{{}}"
            else:
                return f"CAST({quoted_field} AS CHAR) LIKE :{{}}"

    # ============ SELECT 构建 ============

    def build_select(
            self,
            table: str,
            columns: List[str] = None,
            schema: Optional[str] = None,
            database: Optional[str] = None,
            where: Optional[Dict[str, Any]] = None,
            order_by: Optional[str] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """构建 SELECT 语句，返回命名参数"""
        full_table = self.build_table_name(table, schema, database)

        # 列
        if columns:
            cols = ", ".join(self.quote_identifier(c) for c in columns)
        else:
            cols = "*"

        sql = f"SELECT {cols} FROM {full_table}"
        params = {}

        # WHERE
        if where:
            where_clause, where_params = self._build_where_named(where)
            if where_clause:
                sql += f" WHERE {where_clause}"
                params.update(where_params)

        # ORDER BY
        if order_by:
            sql += f" ORDER BY {order_by}"

        # LIMIT / OFFSET
        if limit is not None:
            sql += f" LIMIT {limit}"
            if offset is not None:
                sql += f" OFFSET {offset}"

        return sql, params

    def build_count(
            self,
            table: str,
            schema: Optional[str] = None,
            database: Optional[str] = None,
            where: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """构建 COUNT 查询，返回命名参数"""
        full_table = self.build_table_name(table, schema, database)
        sql = f"SELECT COUNT(*) as total FROM {full_table}"
        params = {}

        if where:
            where_clause, where_params = self._build_where_named(where)
            if where_clause:
                sql += f" WHERE {where_clause}"
                params.update(where_params)

        return sql, params

    # ============ INSERT 构建 ============

    def build_insert(
            self,
            table: str,
            data: Dict[str, Any],
            schema: Optional[str] = None,
            database: Optional[str] = None,
            return_id: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """构建 INSERT 语句，返回 SQL 和命名参数字典"""
        full_table = self.build_table_name(table, schema, database)
        
        # 清理字段名中的空格，并转换数据类型
        cleaned_data = {}
        
        for key, value in data.items():
            cleaned_key = key.strip()
            # 转换日期时间字符串为 Python 对象
            converted_value = self._convert_value(value)
            cleaned_data[cleaned_key] = converted_value
        
        columns = list(cleaned_data.keys())

        cols = ", ".join(self.quote_identifier(c) for c in columns)
        # 使用命名参数 :param_name（使用清理后的字段名）
        placeholders = ", ".join(f":{col}" for col in columns)

        sql = f"INSERT INTO {full_table} ({cols}) VALUES ({placeholders})"

        # 返回自增 ID
        if return_id and self.db_type == "postgresql":
            sql += " RETURNING id"

        return sql, cleaned_data

    def build_batch_insert(
            self,
            table: str,
            columns: List[str],
            rows: List[List[Any]],
            schema: Optional[str] = None,
            database: Optional[str] = None
    ) -> Tuple[str, List[Any]]:
        """构建批量 INSERT 语句"""
        full_table = self.build_table_name(table, schema, database)
        cols = ", ".join(self.quote_identifier(c) for c in columns)

        # 构建多行 VALUES
        row_placeholders = []
        params = []
        param_index = 0

        for row in rows:
            placeholders = ", ".join(self.get_placeholders(len(row), param_index))
            row_placeholders.append(f"({placeholders})")
            params.extend(row)
            param_index += len(row)

        sql = f"INSERT INTO {full_table} ({cols}) VALUES {', '.join(row_placeholders)}"
        return sql, params

    def build_batch_insert_named(
            self,
            table: str,
            data_list: List[Dict[str, Any]],
            schema: Optional[str] = None,
            database: Optional[str] = None
    ) -> Tuple[str, Any]:
        """
        构建批量 INSERT 语句
        
        Args:
            table: 表名
            data_list: 数据列表，每个元素是一个字典
            schema: Schema 名
            database: 数据库名
        
        Returns:
            PostgreSQL: (SQL 语句, 位置参数列表)
            MySQL: (SQL 语句, 命名参数字典)
        """
        if not data_list:
            raise ValueError("data_list 不能为空")
        
        full_table = self.build_table_name(table, schema, database)
        
        # 获取所有列名（使用第一条数据的键）
        columns = list(data_list[0].keys())
        cols = ", ".join(self.quote_identifier(c) for c in columns)
        
        if self.db_type == "postgresql":
            # PostgreSQL 使用位置参数 $1, $2, ...
            row_placeholders = []
            params = []
            param_index = 0
            
            for data in data_list:
                placeholders = []
                for col in columns:
                    placeholders.append(f"${param_index + 1}")
                    # 转换数据类型并添加到参数列表
                    params.append(self._convert_value(data.get(col)))
                    param_index += 1
                row_placeholders.append(f"({', '.join(placeholders)})")
            
            sql = f"INSERT INTO {full_table} ({cols}) VALUES {', '.join(row_placeholders)}"
            return sql, params
        else:
            # MySQL 使用命名参数
            row_placeholders = []
            params = {}
            
            for row_idx, data in enumerate(data_list):
                placeholders = []
                for col in columns:
                    param_name = f"p{row_idx}_{col}"
                    placeholders.append(f":{param_name}")
                    # 转换数据类型
                    params[param_name] = self._convert_value(data.get(col))
                row_placeholders.append(f"({', '.join(placeholders)})")
            
            sql = f"INSERT INTO {full_table} ({cols}) VALUES {', '.join(row_placeholders)}"
            return sql, params

    # ============ UPDATE 构建 ============

    def build_update(
            self,
            table: str,
            data: Dict[str, Any],
            pk_field: str,
            pk_value: Any,
            schema: Optional[str] = None,
            database: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """构建 UPDATE 语句，返回 SQL 和命名参数字典"""
        full_table = self.build_table_name(table, schema, database)

        set_clauses = []
        params = {}
        param_counter = 0

        # 清理字段名中的空格，并转换数据类型
        for col, val in data.items():
            cleaned_col = col.strip()
            # 转换日期时间字符串为 Python 对象
            converted_val = self._convert_value(val)
            param_name = f"param_{param_counter}"
            set_clauses.append(f"{self.quote_identifier(cleaned_col)} = :{param_name}")
            params[param_name] = converted_val
            param_counter += 1

        # 清理主键字段名
        cleaned_pk_field = pk_field.strip()
        pk_param_name = f"param_{param_counter}"
        sql = f"UPDATE {full_table} SET {', '.join(set_clauses)} WHERE {self.quote_identifier(cleaned_pk_field)} = :{pk_param_name}"
        params[pk_param_name] = pk_value

        return sql, params

    # ============ DELETE 构建 ============

    def build_delete(
            self,
            table: str,
            pk_field: str,
            pk_value: Any,
            schema: Optional[str] = None,
            database: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """构建 DELETE 语句，返回 SQL 和命名参数字典"""
        full_table = self.build_table_name(table, schema, database)
        sql = f"DELETE FROM {full_table} WHERE {self.quote_identifier(pk_field)} = :pk_value"
        return sql, {"pk_value": pk_value}

    def build_delete_by_foreign_key(
            self,
            table: str,
            fk_field: str,
            fk_value: Any,
            schema: Optional[str] = None,
            database: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """根据外键删除，返回 SQL 和命名参数字典"""
        full_table = self.build_table_name(table, schema, database)
        sql = f"DELETE FROM {full_table} WHERE {self.quote_identifier(fk_field)} = :fk_value"
        return sql, {"fk_value": fk_value}

    # ============ WHERE 条件构建 ============

    def _build_where_named(self, conditions: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """构建 WHERE 子句（使用命名参数）"""
        clauses = []
        params = {}
        param_counter = 0

        for field, condition in conditions.items():
            if condition is None:
                continue

            # 处理多字段搜索（OR 关系）
            if field == '__search__' and isinstance(condition, dict):
                keyword = condition.get('keyword')
                search_fields = condition.get('fields', [])
                if keyword and search_fields:
                    search_clauses = []
                    for search_field in search_fields:
                        quoted_search_field = self.quote_identifier(search_field)
                        param_name = f"search_param_{param_counter}"
                        # 使用 ILIKE（PostgreSQL）或 LIKE（其他数据库）进行不区分大小写的模糊搜索
                        if self.db_type == "postgresql":
                            search_clauses.append(f"CAST({quoted_search_field} AS TEXT) ILIKE :{param_name}")
                        else:
                            search_clauses.append(f"CAST({quoted_search_field} AS CHAR) LIKE :{param_name}")
                        params[param_name] = f"%{keyword}%"
                        param_counter += 1
                    if search_clauses:
                        clauses.append(f"({' OR '.join(search_clauses)})")
                continue

            quoted_field = self.quote_identifier(field)

            if isinstance(condition, dict):
                cond_type = condition.get("type", "eq")
                value = condition.get("value")

                if cond_type == "like" and value:
                    case_sensitive = condition.get("case_sensitive", True)
                    param_name = f"param_{param_counter}"
                    like_expr = self._build_like_expr(quoted_field, case_sensitive)
                    clauses.append(like_expr.format(param_name))
                    params[param_name] = f"%{value}%"
                    param_counter += 1
                elif cond_type == "eq" and value is not None:
                    param_name = f"param_{param_counter}"
                    case_sensitive = condition.get("case_sensitive", True)
                    if case_sensitive:
                        clauses.append(f"{quoted_field} = :{param_name}")
                    else:
                        clauses.append(f"LOWER({quoted_field}) = LOWER(:{param_name})")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "ne" and value is not None:
                    param_name = f"param_{param_counter}"
                    clauses.append(f"{quoted_field} != :{param_name}")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "gt" and value is not None:
                    param_name = f"param_{param_counter}"
                    clauses.append(f"{quoted_field} > :{param_name}")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "gte" and value is not None:
                    param_name = f"param_{param_counter}"
                    clauses.append(f"{quoted_field} >= :{param_name}")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "lt" and value is not None:
                    param_name = f"param_{param_counter}"
                    clauses.append(f"{quoted_field} < :{param_name}")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "lte" and value is not None:
                    param_name = f"param_{param_counter}"
                    clauses.append(f"{quoted_field} <= :{param_name}")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "range" and value and isinstance(value, list) and len(value) == 2:
                    param_name_start = f"param_{param_counter}"
                    param_name_end = f"param_{param_counter + 1}"
                    clauses.append(f"{quoted_field} BETWEEN :{param_name_start} AND :{param_name_end}")
                    params[param_name_start] = value[0]
                    params[param_name_end] = value[1]
                    param_counter += 2
                elif cond_type == "in" and value:
                    # IN 条件：value 是一个列表
                    if isinstance(value, list) and len(value) > 0:
                        placeholders = []
                        for v in value:
                            param_name = f"param_{param_counter}"
                            placeholders.append(f":{param_name}")
                            params[param_name] = v
                            param_counter += 1
                        clauses.append(f"{quoted_field} IN ({', '.join(placeholders)})")
                elif cond_type == "eq_or_null" and value is not None:
                    # 等值 OR 字段为空（用于数据权限：字段为空时所有人可见）
                    param_name = f"param_{param_counter}"
                    clauses.append(f"({quoted_field} = :{param_name} OR {quoted_field} IS NULL)")
                    params[param_name] = value
                    param_counter += 1
                elif cond_type == "in_or_null" and value:
                    # IN 条件 OR 字段为空（用于数据权限：字段为空时所有人可见）
                    if isinstance(value, list) and len(value) > 0:
                        placeholders = []
                        for v in value:
                            param_name = f"param_{param_counter}"
                            placeholders.append(f":{param_name}")
                            params[param_name] = v
                            param_counter += 1
                        clauses.append(f"({quoted_field} IN ({', '.join(placeholders)}) OR {quoted_field} IS NULL)")
                elif cond_type == "space_like_and" and value:
                    # 空格模糊且：按空格拆分关键词，用 AND + LIKE 连接（范围逐渐缩小）
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            param_name = f"param_{param_counter}"
                            like_expr = self._build_like_expr(quoted_field, case_sensitive)
                            keyword_clauses.append(like_expr.format(param_name))
                            params[param_name] = f"%{keyword}%"
                            param_counter += 1
                        clauses.append(f"({' AND '.join(keyword_clauses)})")
                elif cond_type == "space_like_or" and value:
                    # 空格模糊或：按空格拆分关键词，用 OR + LIKE 连接（范围逐渐扩大）
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            param_name = f"param_{param_counter}"
                            like_expr = self._build_like_expr(quoted_field, case_sensitive)
                            keyword_clauses.append(like_expr.format(param_name))
                            params[param_name] = f"%{keyword}%"
                            param_counter += 1
                        clauses.append(f"({' OR '.join(keyword_clauses)})")
                elif cond_type == "space_eq_and" and value:
                    # 空格精确且：按空格拆分关键词，用 AND + = 连接（范围逐渐缩小）
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            param_name = f"param_{param_counter}"
                            if case_sensitive:
                                keyword_clauses.append(f"{quoted_field} = :{param_name}")
                            else:
                                keyword_clauses.append(f"LOWER({quoted_field}) = LOWER(:{param_name})")
                            params[param_name] = keyword
                            param_counter += 1
                        clauses.append(f"({' AND '.join(keyword_clauses)})")
                elif cond_type == "space_eq_or" and value:
                    # 空格精确或：按空格拆分关键词，用 OR + = 连接（范围逐渐扩大）
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            param_name = f"param_{param_counter}"
                            if case_sensitive:
                                keyword_clauses.append(f"{quoted_field} = :{param_name}")
                            else:
                                keyword_clauses.append(f"LOWER({quoted_field}) = LOWER(:{param_name})")
                            params[param_name] = keyword
                            param_counter += 1
                        clauses.append(f"({' OR '.join(keyword_clauses)})")
                elif cond_type == "null":
                    clauses.append(f"{quoted_field} IS NULL")
                elif cond_type == "not_null":
                    clauses.append(f"{quoted_field} IS NOT NULL")
            else:
                # 简单等值条件
                if condition is not None and condition != "":
                    param_name = f"param_{param_counter}"
                    clauses.append(f"{quoted_field} = :{param_name}")
                    params[param_name] = condition
                    param_counter += 1

        return " AND ".join(clauses), params

    def _build_where(self, conditions: Dict[str, Any], start_index: int = 0) -> Tuple[str, List[Any], int]:
        """
        构建 WHERE 子句
        
        支持的条件格式:
        - {"field": value}  -> field = value
        - {"field": {"type": "like", "value": "xxx"}}  -> field LIKE '%xxx%'
        - {"field": {"type": "eq", "value": xxx}}  -> field = xxx
        - {"field": {"type": "ne", "value": xxx}}  -> field != xxx
        - {"field": {"type": "gt", "value": xxx}}  -> field > xxx
        - {"field": {"type": "gte", "value": xxx}}  -> field >= xxx
        - {"field": {"type": "lt", "value": xxx}}  -> field < xxx
        - {"field": {"type": "lte", "value": xxx}}  -> field <= xxx
        - {"field": {"type": "in", "value": [...]}}  -> field IN (...)
        - {"field": {"type": "range", "value": [start, end]}}  -> field BETWEEN start AND end
        - {"field": {"type": "null"}}  -> field IS NULL
        - {"field": {"type": "not_null"}}  -> field IS NOT NULL
        """
        clauses = []
        params = []
        param_index = start_index

        for field, condition in conditions.items():
            quoted_field = self.quote_identifier(field)

            if condition is None:
                continue

            if isinstance(condition, dict):
                cond_type = condition.get("type", "eq")
                value = condition.get("value")

                if cond_type == "like" and value:
                    case_sensitive = condition.get("case_sensitive", True)
                    if self.db_type == "postgresql":
                        like_op = "LIKE" if case_sensitive else "ILIKE"
                        clauses.append(f"CAST({quoted_field} AS TEXT) {like_op} {self.get_placeholder(param_index)}")
                    else:
                        like_op = "LIKE BINARY" if case_sensitive else "LIKE"
                        clauses.append(f"CAST({quoted_field} AS CHAR) {like_op} {self.get_placeholder(param_index)}")
                    params.append(f"%{value}%")
                    param_index += 1
                elif cond_type == "eq" and value is not None:
                    case_sensitive = condition.get("case_sensitive", True)
                    if case_sensitive:
                        clauses.append(f"{quoted_field} = {self.get_placeholder(param_index)}")
                    else:
                        clauses.append(f"LOWER({quoted_field}) = LOWER({self.get_placeholder(param_index)})")
                    params.append(value)
                    param_index += 1
                elif cond_type == "ne" and value is not None:
                    clauses.append(f"{quoted_field} != {self.get_placeholder(param_index)}")
                    params.append(value)
                    param_index += 1
                elif cond_type == "gt" and value is not None:
                    clauses.append(f"{quoted_field} > {self.get_placeholder(param_index)}")
                    params.append(value)
                    param_index += 1
                elif cond_type == "gte" and value is not None:
                    clauses.append(f"{quoted_field} >= {self.get_placeholder(param_index)}")
                    params.append(value)
                    param_index += 1
                elif cond_type == "lt" and value is not None:
                    clauses.append(f"{quoted_field} < {self.get_placeholder(param_index)}")
                    params.append(value)
                    param_index += 1
                elif cond_type == "lte" and value is not None:
                    clauses.append(f"{quoted_field} <= {self.get_placeholder(param_index)}")
                    params.append(value)
                    param_index += 1
                elif cond_type == "in" and value:
                    placeholders = ", ".join(self.get_placeholders(len(value), param_index))
                    clauses.append(f"{quoted_field} IN ({placeholders})")
                    params.extend(value)
                    param_index += len(value)
                elif cond_type == "range" and value and len(value) == 2:
                    clauses.append(f"{quoted_field} BETWEEN {self.get_placeholder(param_index)} AND {self.get_placeholder(param_index + 1)}")
                    params.extend(value)
                    param_index += 2
                elif cond_type == "space_like_and" and value:
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            if self.db_type == "postgresql":
                                like_op = "LIKE" if case_sensitive else "ILIKE"
                                keyword_clauses.append(f"CAST({quoted_field} AS TEXT) {like_op} {self.get_placeholder(param_index)}")
                            else:
                                like_op = "LIKE BINARY" if case_sensitive else "LIKE"
                                keyword_clauses.append(f"CAST({quoted_field} AS CHAR) {like_op} {self.get_placeholder(param_index)}")
                            params.append(f"%{keyword}%")
                            param_index += 1
                        clauses.append(f"({' AND '.join(keyword_clauses)})")
                elif cond_type == "space_like_or" and value:
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            if self.db_type == "postgresql":
                                like_op = "LIKE" if case_sensitive else "ILIKE"
                                keyword_clauses.append(f"CAST({quoted_field} AS TEXT) {like_op} {self.get_placeholder(param_index)}")
                            else:
                                like_op = "LIKE BINARY" if case_sensitive else "LIKE"
                                keyword_clauses.append(f"CAST({quoted_field} AS CHAR) {like_op} {self.get_placeholder(param_index)}")
                            params.append(f"%{keyword}%")
                            param_index += 1
                        clauses.append(f"({' OR '.join(keyword_clauses)})")
                elif cond_type == "space_eq_and" and value:
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            if case_sensitive:
                                keyword_clauses.append(f"{quoted_field} = {self.get_placeholder(param_index)}")
                            else:
                                keyword_clauses.append(f"LOWER({quoted_field}) = LOWER({self.get_placeholder(param_index)})")
                            params.append(keyword)
                            param_index += 1
                        clauses.append(f"({' AND '.join(keyword_clauses)})")
                elif cond_type == "space_eq_or" and value:
                    case_sensitive = condition.get("case_sensitive", True)
                    keywords = str(value).split()
                    if keywords:
                        keyword_clauses = []
                        for keyword in keywords:
                            if case_sensitive:
                                keyword_clauses.append(f"{quoted_field} = {self.get_placeholder(param_index)}")
                            else:
                                keyword_clauses.append(f"LOWER({quoted_field}) = LOWER({self.get_placeholder(param_index)})")
                            params.append(keyword)
                            param_index += 1
                        clauses.append(f"({' OR '.join(keyword_clauses)})")
                elif cond_type == "null":
                    clauses.append(f"{quoted_field} IS NULL")
                elif cond_type == "not_null":
                    clauses.append(f"{quoted_field} IS NOT NULL")
            else:
                # 简单等值条件
                if condition is not None and condition != "":
                    clauses.append(f"{quoted_field} = {self.get_placeholder(param_index)}")
                    params.append(condition)
                    param_index += 1

        return " AND ".join(clauses), params, param_index
