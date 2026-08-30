"""Form write-back rule CRUD, validation and safe expression evaluation."""

from __future__ import annotations

import ast
import operator as py_operator
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_model import generate_nanoid
from online_dev.form_data_manager.dynamic_sql_builder import DynamicSQLBuilder
from online_dev.form_data_manager.lifecycle import FormLifecycleContext
from online_dev.form_manager.model import FormMeta, FormSubTable, FormWriteBackRule
from online_dev.form_manager.schema import (
    FormWriteBackRuleCreateIn,
    FormWriteBackRuleUpdateIn,
)


class FormWriteBackException(Exception):
    pass


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_EVENT_LABELS = {
    "before_create": "新增前", "after_create": "新增后",
    "before_update": "保存前", "after_update": "保存后",
    "before_delete": "删除前", "after_delete": "删除后",
    "before_approve": "审核前", "after_approve": "审核后",
    "before_unapprove": "反审前", "after_unapprove": "反审后",
}


def _ensure_identifier(value: str, label: str) -> str:
    if not value or not _IDENTIFIER.fullmatch(value):
        raise FormWriteBackException(f"{label}不是合法字段或表名")
    return value


class RowCollection(list):
    """Expression collection which supports ``rows.field`` syntax."""

    def __getattr__(self, field: str) -> List[Any]:
        _ensure_identifier(field, "表达式字段")
        return [row.get(field, 0) for row in self]


def _number(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal(0)
    if isinstance(value, bool):
        return Decimal(int(value))
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise FormWriteBackException(f"表达式中存在非数值字段: {value!r}") from exc


class SafeExpression:
    """Small allow-list AST evaluator; it never evaluates Python source directly."""

    FUNCTIONS = {"count", "sum", "max", "min", "avg"}
    BIN_OPS = {
        ast.Add: py_operator.add,
        ast.Sub: py_operator.sub,
        ast.Mult: py_operator.mul,
        ast.Div: py_operator.truediv,
        ast.Mod: py_operator.mod,
    }

    @classmethod
    def parse(cls, expression: str) -> ast.Expression:
        if not expression or len(expression) > 2000:
            raise FormWriteBackException("自定义表达式不能为空且不能超过 2000 个字符")
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise FormWriteBackException(f"表达式语法错误: {exc.msg}") from exc
        nodes = list(ast.walk(tree))
        if len(nodes) > 100:
            raise FormWriteBackException("表达式过于复杂")
        return tree

    @classmethod
    def validate(cls, expression: str) -> None:
        tree = cls.parse(expression)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in cls.FUNCTIONS:
                    raise FormWriteBackException("只允许调用 count/sum/max/min/avg")
                if node.keywords:
                    raise FormWriteBackException("表达式函数不支持关键字参数")
            elif isinstance(node, ast.Name):
                if node.id not in {"newData", "oldData", "newRows", "oldRows", *cls.FUNCTIONS}:
                    raise FormWriteBackException(f"表达式变量不允许: {node.id}")
            elif isinstance(node, ast.Attribute):
                if not isinstance(node.value, ast.Name) or node.value.id not in {
                    "newData", "oldData", "newRows", "oldRows"
                } or not _IDENTIFIER.fullmatch(node.attr):
                    raise FormWriteBackException("表达式只允许访问 newData/oldData/newRows/oldRows 的字段")
            elif isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.UAdd, ast.USub,
                                   ast.Constant, ast.Load, ast.Add, ast.Sub, ast.Mult,
                                   ast.Div, ast.Mod, ast.Call, ast.Name)):
                continue
            else:
                raise FormWriteBackException(f"表达式语法不允许: {type(node).__name__}")

    @classmethod
    def evaluate(cls, expression: str, context: Dict[str, Any]) -> Any:
        tree = cls.parse(expression)
        cls.validate(expression)

        def visit(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return visit(node.body)
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float, str, bool)) or node.value is None:
                    return node.value
                raise FormWriteBackException("表达式常量类型不允许")
            if isinstance(node, ast.Name):
                return context.get(node.id, 0)
            if isinstance(node, ast.Attribute):
                base = visit(node.value)
                if isinstance(base, dict):
                    return base.get(node.attr, 0)
                if isinstance(base, RowCollection):
                    return getattr(base, node.attr)
                return 0
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = _number(visit(node.operand))
                return value if isinstance(node.op, ast.UAdd) else -value
            if isinstance(node, ast.BinOp) and type(node.op) in cls.BIN_OPS:
                left, right = _number(visit(node.left)), _number(visit(node.right))
                try:
                    return cls.BIN_OPS[type(node.op)](left, right)
                except ZeroDivisionError as exc:
                    raise FormWriteBackException("表达式不能除以 0") from exc
            if isinstance(node, ast.Call):
                values = [visit(arg) for arg in node.args]
                if len(values) != 1:
                    raise FormWriteBackException(f"{node.func.id} 只接受一个参数")
                value = values[0]
                if isinstance(value, RowCollection):
                    values_list = value
                elif isinstance(value, (list, tuple)):
                    values_list = list(value)
                else:
                    values_list = [value]
                fn = node.func.id
                if fn == "count":
                    return len(values_list)
                numbers = [_number(item) for item in values_list]
                if not numbers:
                    return Decimal(0)
                if fn == "sum":
                    return sum(numbers, Decimal(0))
                if fn == "max":
                    return max(numbers)
                if fn == "min":
                    return min(numbers)
                if fn == "avg":
                    return sum(numbers, Decimal(0)) / Decimal(len(numbers))
            raise FormWriteBackException("表达式节点不允许")

        return visit(tree)


class FormWriteBackService:
    """CRUD and runtime executor for rules owned by a source form."""

    @staticmethod
    async def _get_form(db: AsyncSession, form_id: str) -> FormMeta:
        result = await db.execute(select(FormMeta).where(FormMeta.id == form_id, FormMeta.is_deleted == False))
        form = result.scalar_one_or_none()
        if not form:
            raise FormWriteBackException(f"表单不存在: {form_id}")
        return form

    @staticmethod
    async def _get_sub_tables(db: AsyncSession, form_id: str) -> List[FormSubTable]:
        result = await db.execute(select(FormSubTable).where(
            FormSubTable.form_id == form_id, FormSubTable.is_deleted == False
        ))
        # 历史上同一张子表可能被重复写入元数据。回写规则只需要一个表描述，
        # 重复描述会导致同一条规则被重复执行或同一行被重复保存。
        unique: Dict[str, FormSubTable] = {}
        for item in result.scalars().all():
            unique.setdefault(item.table_name, item)
        return list(unique.values())

    @staticmethod
    def _table_config(form: FormMeta, table_key: str) -> Dict[str, Any]:
        if table_key == "main":
            return {"type": "main", "tableName": form.main_table, "fields": []}
        for item in (form.form_config or {}).get("tableConfigs", []):
            if item.get("type") == "sub" and item.get("tableName") == table_key:
                return item
        return {"type": "sub", "tableName": table_key, "fields": []}

    @classmethod
    async def _validate_rule(cls, db: AsyncSession, source_form: FormMeta, payload: Dict[str, Any]) -> Dict[str, Any]:
        target_form = await cls._get_form(db, payload["target_form_id"])
        if target_form.status != "published":
            raise FormWriteBackException("目标表单必须是已发布状态")
        if source_form.db_config != target_form.db_config:
            raise FormWriteBackException("源表单和目标表单必须使用同一个数据库配置")
        source_key = _ensure_identifier(payload["source_table_key"], "源表")
        target_key = _ensure_identifier(payload["target_table_key"], "目标表")
        target_field = _ensure_identifier(payload["target_field"], "目标字段")
        target_config = cls._table_config(target_form, target_key)
        if source_key != "main" and not any(s.table_name == source_key for s in await cls._get_sub_tables(db, source_form.id)):
            raise FormWriteBackException(f"源子表不存在: {source_key}")
        if target_key != "main" and not any(s.table_name == target_key for s in await cls._get_sub_tables(db, target_form.id)):
            raise FormWriteBackException(f"目标子表不存在: {target_key}")
        target_fields = {f.get("name") for f in target_config.get("fields", []) if f.get("name")}
        if target_fields and target_field not in target_fields:
            raise FormWriteBackException(f"目标字段不存在: {target_field}")
        for condition in payload.get("match_conditions") or []:
            _ensure_identifier(condition.get("target_field", ""), "关联目标字段")
            if condition.get("source_field"):
                _ensure_identifier(condition["source_field"], "关联源字段")
        if not payload.get("match_conditions"):
            raise FormWriteBackException("回写规则至少需要一个关联条件")
        if payload["value_mode"] != "custom":
            raise FormWriteBackException("取值方式只支持自定义")
        SafeExpression.validate(payload.get("custom_expression") or "")
        return {**payload, "source_table_key": source_key, "target_table_key": target_key, "target_field": target_field}

    @staticmethod
    def generate_name(target_form: FormMeta, payload: Dict[str, Any]) -> str:
        events = ",".join(_EVENT_LABELS.get(event, event) for event in payload.get("trigger_events", []))
        table = target_form.main_table if payload.get("target_table_key") == "main" else payload.get("target_table_key", "")
        field = payload.get("target_field", "")
        return f"[{events}]更新表[{table}]的[{field}]字段"

    @classmethod
    async def list(cls, db: AsyncSession, source_form_id: str) -> List[Dict[str, Any]]:
        await cls._get_form(db, source_form_id)
        result = await db.execute(select(FormWriteBackRule).where(
            FormWriteBackRule.source_form_id == source_form_id,
            FormWriteBackRule.is_deleted == False,
        ).order_by(FormWriteBackRule.sort, FormWriteBackRule.sys_create_datetime))
        return [{"id": str(item.id), "name": item.name, "enabled": bool(item.enabled)} for item in result.scalars().all()]

    @classmethod
    async def get(cls, db: AsyncSession, source_form_id: str, rule_id: str) -> FormWriteBackRule:
        await cls._get_form(db, source_form_id)
        result = await db.execute(select(FormWriteBackRule).where(
            FormWriteBackRule.id == rule_id,
            FormWriteBackRule.source_form_id == source_form_id,
            FormWriteBackRule.is_deleted == False,
        ))
        rule = result.scalar_one_or_none()
        if not rule:
            raise FormWriteBackException("回写规则不存在")
        return rule

    @classmethod
    async def create(cls, db: AsyncSession, source_form_id: str, data: FormWriteBackRuleCreateIn, user_id: Optional[str]) -> FormWriteBackRule:
        source_form = await cls._get_form(db, source_form_id)
        payload = await cls._validate_rule(db, source_form, data.model_dump())
        target_form = await cls._get_form(db, payload["target_form_id"])
        payload["name"] = cls.generate_name(target_form, payload) if payload.get("is_name_auto", True) else (payload.get("name") or "未命名回写规则")
        rule = FormWriteBackRule(id=generate_nanoid(), source_form_id=source_form_id, **payload, sys_creator_id=user_id, sys_modifier_id=user_id)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @classmethod
    async def update(cls, db: AsyncSession, source_form_id: str, rule_id: str, data: FormWriteBackRuleUpdateIn, user_id: Optional[str]) -> FormWriteBackRule:
        rule = await cls.get(db, source_form_id, rule_id)
        source_form = await cls._get_form(db, source_form_id)
        payload = await cls._validate_rule(db, source_form, data.model_dump())
        target_form = await cls._get_form(db, payload["target_form_id"])
        payload["name"] = cls.generate_name(target_form, payload) if payload.get("is_name_auto", True) else (payload.get("name") or "未命名回写规则")
        for key, value in payload.items():
            setattr(rule, key, value)
        rule.sys_modifier_id = user_id
        await db.commit()
        await db.refresh(rule)
        return rule

    @classmethod
    async def delete(cls, db: AsyncSession, source_form_id: str, rule_id: str, user_id: Optional[str]) -> None:
        rule = await cls.get(db, source_form_id, rule_id)
        rule.is_deleted = True
        rule.sys_modifier_id = user_id
        await db.commit()

    @classmethod
    async def duplicate(cls, db: AsyncSession, source_form_id: str, rule_id: str, user_id: Optional[str]) -> FormWriteBackRule:
        original = await cls.get(db, source_form_id, rule_id)
        payload = {column.name: getattr(original, column.name) for column in FormWriteBackRule.__table__.columns}
        payload.pop("id", None)
        payload.pop("source_form_id", None)
        for key in ("sys_creator_id", "sys_modifier_id", "sys_create_datetime", "sys_update_datetime", "is_deleted", "sort"):
            payload.pop(key, None)
        payload["name"] = f"{original.name}（复制）"
        payload["is_name_auto"] = False
        copied = FormWriteBackRule(id=generate_nanoid(), source_form_id=source_form_id, **payload, sys_creator_id=user_id, sys_modifier_id=user_id)
        db.add(copied)
        await db.commit()
        await db.refresh(copied)
        return copied

    @staticmethod
    def _descriptor(form: FormMeta, sub_tables: List[FormSubTable], table_key: str) -> Dict[str, Any]:
        if table_key == "main":
            table = _ensure_identifier(form.main_table, "数据表")
            schema = _ensure_identifier(form.main_table_schema, "数据表 schema") if form.main_table_schema else None
            database = _ensure_identifier(form.main_table_database, "数据库") if form.main_table_database else None
            return {"table": table, "schema": schema, "database": database}
        for item in sub_tables:
            if item.table_name == table_key:
                table = _ensure_identifier(item.table_name, "数据表")
                schema = _ensure_identifier(item.table_schema, "数据表 schema") if item.table_schema else None
                database = _ensure_identifier(item.table_database, "数据库") if item.table_database else None
                return {"table": table, "schema": schema, "database": database}
        raise FormWriteBackException(f"数据表不存在: {table_key}")

    @staticmethod
    def _builder() -> DynamicSQLBuilder:
        from app.config import settings
        from core.database_manager.service import parse_database_url

        db_info = parse_database_url(settings.DATABASE_URL)
        return DynamicSQLBuilder((db_info or {}).get("db_type", "postgresql"))

    @classmethod
    async def _query_rows(cls, db: AsyncSession, descriptor: Dict[str, Any], lock: bool = False) -> List[Dict[str, Any]]:
        builder = cls._builder()
        table = builder.build_table_name(descriptor["table"], descriptor["schema"], descriptor["database"])
        sql = f"SELECT * FROM {table}"
        if lock:
            sql += " FOR UPDATE"
        result = await db.execute(text(sql))
        return [dict(row._mapping) for row in result.fetchall()]

    @classmethod
    async def _query_source_record(
        cls,
        db: AsyncSession,
        descriptor: Dict[str, Any],
        record_id: Any,
    ) -> Optional[Dict[str, Any]]:
        """读取已落库的源行，避免事件上下文只带了表单投影字段。"""
        if record_id is None:
            return None
        builder = cls._builder()
        table = builder.build_table_name(
            descriptor["table"], descriptor["schema"], descriptor["database"]
        )
        sql = (
            f"SELECT * FROM {table} "
            f"WHERE {builder.quote_identifier('id')} = :source_id LIMIT 1"
        )
        result = await db.execute(text(sql), {"source_id": record_id})
        row = result.first()
        return dict(row._mapping) if row else None

    @staticmethod
    def _condition_value(value: Any, new_data: Dict[str, Any], old_data: Dict[str, Any]) -> Any:
        if isinstance(value, dict) and value.get("from") in ("newData", "oldData"):
            return (new_data if value["from"] == "newData" else old_data).get(value.get("field"), 0)
        return value

    @classmethod
    def _conditions_match(cls, row: Dict[str, Any], conditions: Iterable[Dict[str, Any]], new_data: Dict[str, Any], old_data: Dict[str, Any]) -> bool:
        for condition in conditions or []:
            field, op = condition.get("field"), condition.get("operator", "eq")
            actual = row.get(field)
            expected = cls._condition_value(condition.get("value"), new_data, old_data)
            try:
                if op == "eq" and actual != expected: return False
                if op == "ne" and actual == expected: return False
                if op == "gt" and not actual > expected: return False
                if op == "gte" and not actual >= expected: return False
                if op == "lt" and not actual < expected: return False
                if op == "lte" and not actual <= expected: return False
                if op == "in" and actual not in (expected or []): return False
                if op == "not_in" and actual in (expected or []): return False
                if op == "contains" and str(expected) not in str(actual or ""): return False
                if op == "not_empty" and actual in (None, "", []): return False
            except (TypeError, ValueError):
                return False
        return True

    @classmethod
    def _apply_event_snapshot(cls, current: List[Dict[str, Any]], context: FormLifecycleContext, event: str) -> tuple[RowCollection, RowCollection]:
        current = [dict(row) for row in current]
        old_rows = [dict(row) for row in current]
        new_rows = [dict(row) for row in current]
        record_id = str(context.record_id) if context.record_id is not None else None

        def remove(rows: List[Dict[str, Any]]) -> None:
            rows[:] = [row for row in rows if str(row.get("id")) != record_id]

        def replace(rows: List[Dict[str, Any]], value: Dict[str, Any]) -> None:
            for index, row in enumerate(rows):
                if str(row.get("id")) == record_id:
                    rows[index] = dict(value)
                    return
            if value:
                rows.append(dict(value))

        if event.startswith("before_"):
            if event.endswith("create"):
                remove(new_rows)
                if context.data: new_rows.append(dict(context.data))
            elif event.endswith("update"):
                replace(new_rows, context.data)
            elif event.endswith("delete"):
                remove(new_rows)
            elif event.endswith("approve") or event.endswith("unapprove"):
                replace(new_rows, context.data)
        elif event.startswith("after_"):
            if event.endswith("create"):
                remove(old_rows)
                if context.data: replace(new_rows, context.data)
            elif event.endswith("update") or event.endswith("approve") or event.endswith("unapprove"):
                replace(old_rows, context.old_data)
                replace(new_rows, context.data)
            elif event.endswith("delete"):
                new_rows = [row for row in current if str(row.get("id")) != record_id]
                if context.old_data: old_rows.append(dict(context.old_data))
        return RowCollection(new_rows), RowCollection(old_rows)

    @classmethod
    async def _find_targets(cls, db: AsyncSession, target: FormMeta, target_subs: List[FormSubTable], rule: FormWriteBackRule, source_row: Dict[str, Any]) -> List[Dict[str, Any]]:
        descriptor = cls._descriptor(target, target_subs, rule.target_table_key)
        builder = cls._builder()
        table = builder.build_table_name(descriptor["table"], descriptor["schema"], descriptor["database"])
        clauses, params = [], {}
        for index, item in enumerate(rule.match_conditions or []):
            target_field = _ensure_identifier(item.get("target_field", ""), "关联目标字段")
            if item.get("source_field"):
                source_field = item["source_field"]
                if source_field not in source_row:
                    raise FormWriteBackException(
                        f"规则「{rule.name}」关联源字段「{source_field}」不在当前源数据中"
                    )
                value = source_row.get(source_field)
            else:
                value = item.get("fixed_value")
            if value is None:
                clauses.append(f"{builder.quote_identifier(target_field)} IS NULL")
            else:
                key = f"match_{index}"
                clauses.append(f"{builder.quote_identifier(target_field)} = :{key}")
                params[key] = value
        if not clauses:
            raise FormWriteBackException("回写规则至少需要一个关联条件")
        sql = f"SELECT * FROM {table} WHERE {' AND '.join(clauses)} LIMIT 2"
        if builder.db_type in ("postgresql", "mysql"):
            sql += " FOR UPDATE"
        result = await db.execute(text(sql), params)
        return [dict(row._mapping) for row in result.fetchall()]

    @classmethod
    async def _update_target(cls, db: AsyncSession, target: FormMeta, target_subs: List[FormSubTable], rule: FormWriteBackRule, target_row: Dict[str, Any], value: Any) -> None:
        field = _ensure_identifier(rule.target_field, "目标字段")
        if rule.writeback_operator == "set":
            result_value = value
        else:
            current = _number(target_row.get(field))
            amount = _number(value)
            result_value = current + amount if rule.writeback_operator == "add" else current - amount
        descriptor = cls._descriptor(target, target_subs, rule.target_table_key)
        builder = cls._builder()
        table = builder.build_table_name(descriptor["table"], descriptor["schema"], descriptor["database"])
        sql = f"UPDATE {table} SET {builder.quote_identifier(field)} = :writeback_value WHERE {builder.quote_identifier('id')} = :target_id"
        await db.execute(text(sql), {"writeback_value": result_value, "target_id": target_row.get("id")})

    @classmethod
    async def dispatch(cls, context: FormLifecycleContext, event: str) -> None:
        """Execute all matching enabled rules inside the caller transaction."""
        from contextvars import ContextVar
        active: ContextVar[set] = getattr(cls, "_active", None)
        if active is None:
            active = ContextVar("form_writeback_active", default=set())
            cls._active = active
        source_form_result = await context.db.execute(select(FormMeta).where(FormMeta.code == context.form_code, FormMeta.is_deleted == False))
        source = source_form_result.scalar_one_or_none()
        if not source:
            return
        rules_result = await context.db.execute(select(FormWriteBackRule).where(
            FormWriteBackRule.source_form_id == source.id,
            FormWriteBackRule.enabled == True,
            FormWriteBackRule.is_deleted == False,
        ))
        source_subs = await cls._get_sub_tables(context.db, source.id)
        for rule in rules_result.scalars().all():
            if event not in (rule.trigger_events or []):
                continue
            # 一条规则的源表决定了它监听哪一个表级生命周期钩子。
            # 例如源表是 purchase_in_item 时，主表 purchase_in 的
            # after_create 不能执行这条规则，否则上下文里不会有
            # purchase_order_item_id，最终会被误判为目标记录不存在。
            hook_table_key = "main" if context.table_type == "main" else context.table_name
            if hook_table_key != rule.source_table_key:
                continue
            token_key = (str(rule.id), context.form_code, context.table_name, str(context.record_id))
            current_active = active.get()
            if token_key in current_active:
                continue
            active_token = active.set(current_active | {token_key})
            try:
                effective_old = dict(context.old_data or {})
                effective_new = dict(context.data or {})
                if event.endswith("delete"):
                    effective_new = {}
                if event.startswith("before_") and event.endswith(("approve", "unapprove")):
                    effective_new["sys_audit_status"] = "pending" if event.endswith("unapprove") else "approved"
                if not cls._conditions_match(effective_new or effective_old, rule.execute_conditions or [], effective_new, effective_old):
                    continue
                source_descriptor = cls._descriptor(source, source_subs, rule.source_table_key)
                source_row = dict(effective_new or effective_old)
                # after_create/after_update 等事件的上下文通常来自落库后的完整行，
                # 但某些调用方只传了表单可见字段。按源表和记录 ID 再读取一次，
                # 保证关联字段（例如 purchase_order_item_id）不会因投影缺失而变成空值。
                source_record_id = None
                if rule.source_table_key == "main":
                    source_record_id = context.main_record_id or context.record_id
                elif context.table_name == rule.source_table_key:
                    source_record_id = context.record_id
                persisted_source = await cls._query_source_record(
                    context.db, source_descriptor, source_record_id
                )
                if persisted_source:
                    source_row = {**source_row, **persisted_source}
                if "id" not in source_row and source_record_id is not None:
                    source_row["id"] = source_record_id
                current_rows = await cls._query_rows(context.db, source_descriptor)
                new_rows, old_rows = cls._apply_event_snapshot(current_rows, context, event)
                target = await cls._get_form(context.db, rule.target_form_id)
                target_subs = await cls._get_sub_tables(context.db, target.id)
                targets = await cls._find_targets(context.db, target, target_subs, rule, source_row)
                if len(targets) == 0:
                    raise FormWriteBackException(f"规则「{rule.name}」未找到目标记录")
                if len(targets) > 1:
                    raise FormWriteBackException(f"规则「{rule.name}」匹配到多条目标记录")
                target_row = targets[0]
                filtered_new = RowCollection(row for row in new_rows if cls._conditions_match(row, rule.value_filter_conditions or [], effective_new, effective_old))
                filtered_old = RowCollection(row for row in old_rows if cls._conditions_match(row, rule.value_filter_conditions or [], effective_new, effective_old))
                expression = rule.custom_expression or ""
                # 兼容早期版本创建的 direct/sum 规则；新规则统一走安全自定义表达式。
                if not expression and rule.source_value_field and _IDENTIFIER.fullmatch(rule.source_value_field):
                    expression = (
                        f"sum(newRows.{rule.source_value_field})"
                        if rule.value_mode == "sum"
                        else f"newData.{rule.source_value_field}"
                    )
                value = SafeExpression.evaluate(expression, {"newData": effective_new, "oldData": effective_old, "newRows": filtered_new, "oldRows": filtered_old})
                await cls._update_target(context.db, target, target_subs, rule, target_row, value)
            finally:
                active.reset(active_token)


def serialize_rule(rule: FormWriteBackRule) -> Dict[str, Any]:
    return {
        "id": str(rule.id), "source_form_id": str(rule.source_form_id), "target_form_id": str(rule.target_form_id),
        "name": rule.name, "is_name_auto": bool(rule.is_name_auto), "enabled": bool(rule.enabled),
        "source_table_key": rule.source_table_key, "target_table_key": rule.target_table_key,
        "target_field": rule.target_field, "trigger_events": rule.trigger_events or [],
        "value_mode": "custom",
        "custom_expression": rule.custom_expression or (
            f"sum(newRows.{rule.source_value_field})"
            if rule.value_mode == "sum" and rule.source_value_field and _IDENTIFIER.fullmatch(rule.source_value_field)
            else f"newData.{rule.source_value_field}"
            if rule.source_value_field and _IDENTIFIER.fullmatch(rule.source_value_field)
            else ""
        ),
        "writeback_operator": rule.writeback_operator, "execute_conditions": rule.execute_conditions or [],
        "value_filter_conditions": rule.value_filter_conditions or [], "match_conditions": rule.match_conditions or [],
        "missing_target_policy": rule.missing_target_policy, "remark": rule.remark or "",
        "sys_create_datetime": rule.sys_create_datetime.strftime("%Y-%m-%d %H:%M:%S") if rule.sys_create_datetime else None,
        "sys_update_datetime": rule.sys_update_datetime.strftime("%Y-%m-%d %H:%M:%S") if rule.sys_update_datetime else None,
    }
