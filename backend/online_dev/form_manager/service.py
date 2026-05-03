#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
表单元数据管理服务（异步版本）

数据权限：
- 使用 list_with_data_scope() 自动应用数据权限
- 支持本人、本部门、本部门及下级、全部等数据范围
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.application.model import Application
from online_dev.form_manager.model import FormMeta, FormSubTable
from app.data_scope_utils import get_data_scope_filter, apply_data_scope_to_conditions

logger = logging.getLogger(__name__)

# 资源类型（用于数据权限配置）
RESOURCE_TYPE = "form"
RESOURCE_DISPLAY_NAME = "表单管理"


class FormServiceException(Exception):
    """表单服务异常"""
    pass


class FormService:
    """表单元数据管理服务"""

    # ============ 查询 ============

    @staticmethod
    async def list(
            db: AsyncSession,
            page: int = 1,
            page_size: int = 20,
            application_id: str = None,
            name: str = None,
            code: str = None,
            form_type: str = None,
            status: str = None
    ) -> Dict[str, Any]:
        """分页查询表单列表（包含应用名称）"""
        conditions = [FormMeta.is_deleted == False]

        # 应用过滤
        if application_id:
            conditions.append(FormMeta.application_id == application_id)
        else:
            # 如果没有指定 application_id，只返回主应用的表单（application_id 为 NULL）
            conditions.append(FormMeta.application_id.is_(None))

        if name:
            conditions.append(FormMeta.name.ilike(f"%{name}%"))
        if code:
            conditions.append(FormMeta.code.ilike(f"%{code}%"))
        if form_type:
            conditions.append(FormMeta.form_type == form_type)
        if status:
            conditions.append(FormMeta.status == status)

        # 获取总数
        count_stmt = select(func.count(FormMeta.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表（使用 LEFT JOIN 查询应用名称和编码）
        offset = (page - 1) * page_size
        stmt = (
            select(
                FormMeta,
                Application.name.label('application_name'),
                Application.code.label('application_code'),
            )
            .outerjoin(Application, FormMeta.application_id == Application.id)
            .where(and_(*conditions))
            .order_by(FormMeta.sort, FormMeta.sys_create_datetime.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        items = []
        for form, app_name, app_code in result:
            form.application_name = app_name or "主应用"
            form.application_code = app_code or ""
            items.append(form)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    async def list_with_data_scope(
            db: AsyncSession,
            page: int = 1,
            page_size: int = 20,
            application_id: str = None,
            name: str = None,
            code: str = None,
            form_type: str = None,
            status: str = None
    ) -> Dict[str, Any]:
        """
        分页查询表单列表（带数据权限过滤）
        
        自动从上下文获取当前用户信息，应用数据权限过滤
        """
        conditions = [FormMeta.is_deleted == False]

        # 应用过滤
        if application_id:
            conditions.append(FormMeta.application_id == application_id)
        else:
            conditions.append(FormMeta.application_id.is_(None))

        if name:
            conditions.append(FormMeta.name.ilike(f"%{name}%"))
        if code:
            conditions.append(FormMeta.code.ilike(f"%{code}%"))
        if form_type:
            conditions.append(FormMeta.form_type == form_type)
        if status:
            conditions.append(FormMeta.status == status)

        # 获取数据权限过滤条件并应用
        data_scope_filter = await get_data_scope_filter(db, RESOURCE_TYPE)
        scope_conditions = apply_data_scope_to_conditions(FormMeta, data_scope_filter)
        conditions.extend(scope_conditions)

        # 获取总数
        count_stmt = select(func.count(FormMeta.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表（使用 LEFT JOIN 查询应用名称和编码）
        offset = (page - 1) * page_size
        stmt = (
            select(
                FormMeta,
                Application.name.label('application_name'),
                Application.code.label('application_code'),
            )
            .outerjoin(Application, FormMeta.application_id == Application.id)
            .where(and_(*conditions))
            .order_by(FormMeta.sort, FormMeta.sys_create_datetime.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        items = []
        for form, app_name, app_code in result:
            form.application_name = app_name or "主应用"
            form.application_code = app_code or ""
            items.append(form)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    async def get(db: AsyncSession, form_id: str) -> FormMeta:
        """获取表单详情"""
        stmt = select(FormMeta).where(
            FormMeta.id == form_id,
            FormMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            raise FormServiceException(f"表单不存在: {form_id}")

        return form

    @staticmethod
    async def get_sub_tables(db: AsyncSession, form_id: str) -> List[FormSubTable]:
        """获取表单子表配置"""
        stmt = select(FormSubTable).where(
            FormSubTable.form_id == form_id,
            FormSubTable.is_deleted == False
        ).order_by(FormSubTable.sort)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> FormMeta:
        """根据编码获取表单"""
        stmt = select(FormMeta).where(
            FormMeta.code == code,
            FormMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            raise FormServiceException(f"表单不存在: {code}")

        return form

    # ============ 创建 ============

    @staticmethod
    async def create(
            db: AsyncSession,
            data: Dict[str, Any],
            user_id: str = None
    ) -> FormMeta:
        """创建表单"""
        code = data.get("code")

        # 检查编码唯一性
        stmt = select(FormMeta).where(
            FormMeta.code == code,
            FormMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise FormServiceException(f"表单编码已存在: {code}")

        sub_tables_data = data.pop("sub_tables", [])

        # 从上下文获取用户信息
        from utils.context import get_current_user_info_from_context
        user_info = get_current_user_info_from_context()
        creator_id = user_id or (user_info.get('user_id') if user_info else None)
        dept_id = user_info.get('dept_id') if user_info else None

        # 创建主表单
        form = FormMeta(
            application_id=data.get("application_id"),
            name=data.get("name"),
            code=code,
            form_type=data.get("form_type", "normal"),
            description=data.get("description", ""),
            db_config=data.get("db_config"),
            main_table=data.get("main_table"),
            main_table_schema=data.get("main_table_schema", ""),
            main_table_database=data.get("main_table_database", ""),
            form_config=data.get("form_config", {}),
            list_config=data.get("list_config", {}),
            sort=data.get("sort", 0),
            sys_creator_id=creator_id,
            sys_modifier_id=creator_id,
            sys_dept_id=dept_id,
        )
        db.add(form)
        await db.flush()

        # 创建子表关联
        for idx, sub_data in enumerate(sub_tables_data):
            sub_table = FormSubTable(
                form_id=form.id,
                table_name=sub_data.get("table_name"),
                table_schema=sub_data.get("table_schema", ""),
                table_database=sub_data.get("table_database", ""),
                alias=sub_data.get("alias", ""),
                foreign_key=sub_data.get("foreign_key"),
                related_field=sub_data.get("related_field", "id"),
                relation_type=sub_data.get("relation_type", "one-to-many"),
                sort=sub_data.get("sort", idx),
                sys_creator_id=user_id,
                sys_modifier_id=user_id,
            )
            db.add(sub_table)

        await db.commit()
        await db.refresh(form)

        logger.info(f"表单创建成功: {form.code}")
        return form

    # ============ 更新 ============

    @staticmethod
    async def update(
            db: AsyncSession,
            form_id: str,
            data: Dict[str, Any],
            user_id: str = None
    ) -> FormMeta:
        """更新表单"""
        form = await FormService.get(db, form_id)

        # 更新基本字段
        if "name" in data and data["name"] is not None:
            form.name = data["name"]
        if "form_type" in data and data["form_type"] is not None:
            form.form_type = data["form_type"]
        if "description" in data and data["description"] is not None:
            form.description = data["description"]
        if "sort" in data and data["sort"] is not None:
            form.sort = data["sort"]
        if "show_in_mobile" in data and data["show_in_mobile"] is not None:
            form.show_in_mobile = data["show_in_mobile"]
        if "icon" in data and data["icon"] is not None:
            form.icon = data["icon"]
        if "icon_bg_color" in data and data["icon_bg_color"] is not None:
            form.icon_bg_color = data["icon_bg_color"]
        if "form_config" in data and data["form_config"] is not None:
            form.form_config = data["form_config"]
        if "list_config" in data and data["list_config"] is not None:
            form.list_config = data["list_config"]
        
        # 更新数据库配置字段
        if "db_config" in data and data["db_config"] is not None:
            form.db_config = data["db_config"]
        if "main_table" in data and data["main_table"] is not None:
            form.main_table = data["main_table"]
        if "main_table_schema" in data and data["main_table_schema"] is not None:
            form.main_table_schema = data["main_table_schema"]
        if "main_table_database" in data and data["main_table_database"] is not None:
            form.main_table_database = data["main_table_database"]

        form.sys_modifier_id = user_id

        # 更新子表关联
        if "sub_tables" in data and data["sub_tables"] is not None:
            # 删除现有子表关联
            delete_stmt = update(FormSubTable).where(
                FormSubTable.form_id == form_id
            ).values(is_deleted=True)
            await db.execute(delete_stmt)

            # 创建新的子表关联
            for idx, sub_data in enumerate(data["sub_tables"]):
                sub_table = FormSubTable(
                    form_id=form_id,
                    table_name=sub_data.get("table_name"),
                    table_schema=sub_data.get("table_schema", ""),
                    table_database=sub_data.get("table_database", ""),
                    alias=sub_data.get("alias", ""),
                    foreign_key=sub_data.get("foreign_key"),
                    related_field=sub_data.get("related_field", "id"),
                    relation_type=sub_data.get("relation_type", "one-to-many"),
                    sort=sub_data.get("sort", idx),
                    sys_creator_id=user_id,
                    sys_modifier_id=user_id,
                )
                db.add(sub_table)

        await db.commit()
        await db.refresh(form)

        logger.info(f"表单更新成功: {form.code}")
        return form

    # ============ 删除 ============

    @staticmethod
    async def delete(db: AsyncSession, form_id: str) -> bool:
        """删除表单（物理删除）"""
        form = await FormService.get(db, form_id)

        # 物理删除子表关联
        from sqlalchemy import delete as sql_delete
        delete_sub_stmt = sql_delete(FormSubTable).where(
            FormSubTable.form_id == form_id
        )
        await db.execute(delete_sub_stmt)

        # 物理删除表单
        await db.delete(form)
        await db.commit()

        logger.info(f"表单删除成功: {form.code}")
        return True

    @staticmethod
    async def batch_delete(db: AsyncSession, form_ids: List[str]) -> int:
        """批量删除表单（物理删除）"""
        from sqlalchemy import delete as sql_delete
        
        # 物理删除子表关联
        delete_sub_stmt = sql_delete(FormSubTable).where(
            FormSubTable.form_id.in_(form_ids)
        )
        await db.execute(delete_sub_stmt)

        # 物理删除表单
        delete_stmt = sql_delete(FormMeta).where(
            FormMeta.id.in_(form_ids),
            FormMeta.is_deleted == False
        )
        result = await db.execute(delete_stmt)
        await db.commit()

        count = result.rowcount
        logger.info(f"批量删除表单成功: {count} 个")
        return count

    # ============ 发布/取消发布 ============

    @staticmethod
    async def publish(
            db: AsyncSession,
            form_id: str,
            publish_config: Dict[str, Any] = None
    ) -> FormMeta:
        """发布表单并创建菜单和权限"""
        from core.menu.model import Menu
        from core.menu.service import MenuService
        from core.permission.model import Permission

        form = await FormService.get(db, form_id)

        if form.status == "published":
            raise FormServiceException("表单已发布")

        # 更新表单状态
        form.status = "published"
        form.version += 1

        # 保存发布配置到 list_config
        if publish_config:
            list_config = form.list_config or {}
            list_config["publish_config"] = {
                "allow_add": publish_config.get("allow_add", True),
                "allow_edit": publish_config.get("allow_edit", True),
                "allow_delete": publish_config.get("allow_delete", True),
                "allow_export": publish_config.get("allow_export", True),
                "allow_import": publish_config.get("allow_import", False),
            }
            form.list_config = list_config

        # 创建或更新菜单
        menu_record = None
        if publish_config:
            menu_parent_id = publish_config.get("menu_parent_id")

            # 检查是否已存在该表单的菜单
            menu_stmt = select(Menu).where(
                Menu.path == f"/form-render/{form.code}"
            )
            menu_result = await db.execute(menu_stmt)
            existing_menu = menu_result.scalar_one_or_none()

            if existing_menu:
                # 更新现有菜单
                existing_menu.name = publish_config.get("menu_name", form.name)
                existing_menu.title = publish_config.get("menu_name", form.name)
                existing_menu.parent_id = menu_parent_id
                existing_menu.icon = publish_config.get("menu_icon", "lucide:file-text")
                existing_menu.order = publish_config.get("menu_order", 0)
                existing_menu.type = "online_form"
                existing_menu.application_id = form.application_id
                menu_record = existing_menu
                logger.info(f"更新表单菜单: {form.code}")
            else:
                # 创建新菜单
                new_menu = Menu(
                    application_id=form.application_id,
                    name=publish_config.get("menu_name", form.name),
                    title=publish_config.get("menu_name", form.name),
                    path=f"/form-render/{form.code}",
                    component="online-dev/form-render/index",
                    type="online_form",
                    parent_id=menu_parent_id,
                    icon=publish_config.get("menu_icon", "lucide:file-text"),
                    order=publish_config.get("menu_order", 0),
                )
                db.add(new_menu)
                await db.flush()
                menu_record = new_menu
                logger.info(f"创建表单菜单: {form.code}")

        # 创建表单操作权限
        if menu_record:
            await FormService._create_form_permissions(
                db, form, menu_record.id, publish_config
            )

        await db.commit()
        await db.refresh(form)

        # 清空菜单缓存
        await MenuService.invalidate_cache()
        logger.info("已清空菜单缓存")

        logger.info(f"表单发布成功: {form.code}, version={form.version}")
        return form

    @staticmethod
    async def _create_form_permissions(
            db: AsyncSession,
            form: FormMeta,
            menu_id: str,
            publish_config: Dict[str, Any] = None
    ):
        """创建表单操作权限"""
        from core.permission.model import Permission
        from app.resource_registry import ResourceRegistry

        # 注册表单资源类型到资源注册表（用于数据权限和字段权限配置）
        resource_type = f"form:{form.code}"
        # 生成字段元数据
        field_metadata = FormService._generate_form_field_metadata(form)
        ResourceRegistry.register(
            resource_type=resource_type,
            service_class=None,  # 表单没有对应的 Service 类
            display_name=form.name,
            application_id=form.application_id,
            field_metadata=field_metadata
        )
        logger.info(f"注册表单资源类型: {resource_type}, application_id={form.application_id}, fields={len(field_metadata)}")

        # 定义标准操作权限
        actions = [
            ("view", "查看", True, 0, "GET"),
            ("add", "新增", publish_config.get("allow_add", True) if publish_config else True, 1, "POST"),
            ("edit", "编辑", publish_config.get("allow_edit", True) if publish_config else True, 2, "PUT"),
            ("delete", "删除", publish_config.get("allow_delete", True) if publish_config else True, 3, "DELETE"),
            ("export", "导出", publish_config.get("allow_export", True) if publish_config else True, 1, "POST"),
            ("import", "导入", publish_config.get("allow_import", False) if publish_config else False, 1, "POST"),
        ]

        # HTTP 方法映射
        http_method_map = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3, "PATCH": 4, "ALL": 5}

        for action, name, enabled, http_method_int, http_method_str in actions:
            perm_code = f"form:{form.code}:{action}"

            # 检查权限是否已存在
            existing_stmt = select(Permission).where(
                Permission.menu_id == menu_id,
                Permission.code == perm_code,
                Permission.is_deleted == False
            )
            existing_result = await db.execute(existing_stmt)
            existing_perm = existing_result.scalar_one_or_none()

            if existing_perm:
                # 更新现有权限的启用状态
                existing_perm.is_active = enabled
                existing_perm.name = f"{form.name}-{name}"
                logger.info(f"更新表单权限: {perm_code}, enabled={enabled}")
            else:
                # 创建新权限
                perm = Permission(
                    menu_id=menu_id,
                    name=f"{form.name}-{name}",
                    code=perm_code,
                    permission_type=1,  # API权限
                    api_path=f"/api/core/form-data/{form.code}",
                    http_method=http_method_int,
                    is_active=enabled,
                    sort=actions.index((action, name, enabled, http_method_int, http_method_str))
                )
                db.add(perm)
                logger.info(f"创建表单权限: {perm_code}, enabled={enabled}")

    @staticmethod
    async def unpublish(db: AsyncSession, form_id: str) -> FormMeta:
        """取消发布表单并删除菜单、权限等相关数据"""
        from core.menu.model import Menu
        from core.menu.service import MenuService
        from core.permission.model import Permission
        from core.resource_scope.field_permission.model import ResourceFieldPermissionConfig
        from core.resource_scope.scope_permission.model import ResourceDataScopeConfig
        from app.resource_registry import ResourceRegistry

        form = await FormService.get(db, form_id)

        if form.status == "draft":
            raise FormServiceException("表单未发布")

        form.status = "draft"
        resource_type = f"form:{form.code}"

        # 1. 物理删除对应菜单
        delete_menu_stmt = delete(Menu).where(
            Menu.path == f"/form-render/{form.code}"
        )
        menu_result = await db.execute(delete_menu_stmt)
        if menu_result.rowcount > 0:
            logger.info(f"物理删除表单菜单: {form.code}, 删除数量: {menu_result.rowcount}")

        # 2. 物理删除 API 权限（权限 code 以 form:{form_code}: 开头）
        delete_perm_stmt = delete(Permission).where(
            Permission.code.like(f"form:{form.code}:%")
        )
        perm_result = await db.execute(delete_perm_stmt)
        if perm_result.rowcount > 0:
            logger.info(f"物理删除表单API权限: {form.code}, 删除数量: {perm_result.rowcount}")

        # 3. 物理删除字段权限配置
        delete_field_perm_stmt = delete(ResourceFieldPermissionConfig).where(
            ResourceFieldPermissionConfig.resource_type == resource_type
        )
        field_perm_result = await db.execute(delete_field_perm_stmt)
        if field_perm_result.rowcount > 0:
            logger.info(f"物理删除表单字段权限: {form.code}, 删除数量: {field_perm_result.rowcount}")

        # 4. 物理删除数据权限配置
        delete_scope_stmt = delete(ResourceDataScopeConfig).where(
            ResourceDataScopeConfig.resource_type == resource_type
        )
        scope_result = await db.execute(delete_scope_stmt)
        if scope_result.rowcount > 0:
            logger.info(f"物理删除表单数据权限: {form.code}, 删除数量: {scope_result.rowcount}")

        # 5. 从资源注册表中移除
        if ResourceRegistry.unregister(resource_type):
            logger.info(f"从资源注册表移除: {resource_type}")

        await db.commit()
        await db.refresh(form)

        # 清空菜单缓存
        await MenuService.invalidate_cache()
        logger.info("已清空菜单缓存")

        logger.info(f"表单取消发布完成: {form.code}")
        return form

    # ============ 复制 ============

    @staticmethod
    async def copy(
            db: AsyncSession,
            form_id: str,
            new_code: str,
            new_name: str = None,
            user_id: str = None
    ) -> FormMeta:
        """复制表单"""
        source = await FormService.get(db, form_id)

        # 检查新编码唯一性
        stmt = select(FormMeta).where(
            FormMeta.code == new_code,
            FormMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise FormServiceException(f"表单编码已存在: {new_code}")

        # 创建新表单
        new_form = FormMeta(
            name=new_name or f"{source.name}_副本",
            code=new_code,
            form_type=source.form_type,
            description=source.description,
            status="draft",
            version=1,
            db_config=source.db_config,
            main_table=source.main_table,
            main_table_schema=source.main_table_schema,
            main_table_database=source.main_table_database,
            form_config=source.form_config,
            list_config=source.list_config,
            sort=source.sort,
            sys_creator_id=user_id,
            sys_modifier_id=user_id,
        )
        db.add(new_form)
        await db.flush()

        # 复制子表关联
        sub_tables = await FormService.get_sub_tables(db, form_id)
        for sub in sub_tables:
            new_sub = FormSubTable(
                form_id=new_form.id,
                table_name=sub.table_name,
                table_schema=sub.table_schema,
                table_database=sub.table_database,
                alias=sub.alias,
                foreign_key=sub.foreign_key,
                related_field=sub.related_field,
                relation_type=sub.relation_type,
                sort=sub.sort,
                sys_creator_id=user_id,
                sys_modifier_id=user_id,
            )
            db.add(new_sub)

        await db.commit()
        await db.refresh(new_form)

        logger.info(f"表单复制成功: {source.code} -> {new_code}")
        return new_form

    # ============ 导入/导出 ============

    @staticmethod
    async def export_config(db: AsyncSession, form_id: str) -> Dict[str, Any]:
        """导出表单配置"""
        form = await FormService.get(db, form_id)
        sub_tables = await FormService.get_sub_tables(db, form_id)

        sub_tables_data = []
        for sub in sub_tables:
            sub_tables_data.append({
                "table_name": sub.table_name,
                "table_schema": sub.table_schema,
                "table_database": sub.table_database,
                "alias": sub.alias,
                "foreign_key": sub.foreign_key,
                "related_field": sub.related_field,
                "relation_type": sub.relation_type,
                "sort": sub.sort
            })

        return {
            "name": form.name,
            "code": form.code,
            "form_type": form.form_type,
            "description": form.description,
            "db_config": form.db_config,
            "main_table": form.main_table,
            "main_table_schema": form.main_table_schema,
            "main_table_database": form.main_table_database,
            "form_config": form.form_config,
            "list_config": form.list_config,
            "sub_tables": sub_tables_data
        }

    @staticmethod
    async def import_config(
            db: AsyncSession,
            data: Dict[str, Any],
            user_id: str = None
    ) -> FormMeta:
        """导入表单配置"""
        required_fields = ["name", "code", "db_config", "main_table"]
        for field in required_fields:
            if not data.get(field):
                raise FormServiceException(f"缺少必要字段: {field}")

        return await FormService.create(db, data, user_id)

    # ============ 获取表单类型列表 ============

    @staticmethod
    def get_form_types() -> List[Dict[str, str]]:
        """获取所有表单类型"""
        return [
            {"value": "normal", "label": "普通表单"},
            {"value": "workflow", "label": "流程表单"},
        ]

    @staticmethod
    def _generate_form_field_metadata(form: FormMeta) -> Dict[str, Dict[str, Any]]:
        """
        根据表单配置生成字段元数据
        用于字段权限配置
        """
        field_metadata = {}
        
        # 从表单配置中提取字段信息
        form_config = form.form_config or {}
        items = form_config.get('items', [])
        
        def extract_fields(items_list):
            """递归提取字段信息"""
            for item in items_list:
                field_name = item.get('field')
                item_type = item.get('type', '')
                
                # 处理容器类型，递归提取子项
                # collapse: 子项在 items[].children 中
                if item_type == 'collapse':
                    collapse_items = item.get('items', [])
                    for collapse_item in collapse_items:
                        collapse_children = collapse_item.get('children', [])
                        if collapse_children:
                            extract_fields(collapse_children)
                    continue
                
                # grid: 子项在 columns[].children 中
                if item_type == 'grid':
                    columns = item.get('columns', [])
                    for column in columns:
                        column_children = column.get('children', [])
                        if column_children:
                            extract_fields(column_children)
                    continue
                
                # tabs: 子项在 tabs[].children 中
                if item_type == 'tabs':
                    tabs = item.get('tabs', [])
                    for tab in tabs:
                        tab_children = tab.get('children', [])
                        if tab_children:
                            extract_fields(tab_children)
                    continue
                
                # 其他容器类型（card, row, col, 展示组件等）: 子项在 children 中
                if item_type in ['card', 'row', 'col', 'divider', 'alert', 'timeline', 'text', 'html', 'spacer', 'title', 'steps']:
                    children = item.get('children', [])
                    if children:
                        extract_fields(children)
                    continue
                
                # sub-table: 子表字段也需要提取
                if item_type == 'sub-table':
                    # 子表本身作为一个字段
                    if field_name and not field_name.startswith('_'):
                        field_metadata[field_name] = {
                            'label': item.get('label', field_name),
                            'field_type': 'sub-table',
                            'required': item.get('props', {}).get('required', False),
                            'sensitive': False,
                            'maskable': False,
                            'default_permission': 'write'
                        }
                    # 子表内的字段也提取
                    children = item.get('children', [])
                    if children:
                        extract_fields(children)
                    continue
                
                # 跳过没有字段名的项
                if not field_name:
                    continue
                
                # 跳过内部字段
                if field_name.startswith('_'):
                    continue
                
                field_metadata[field_name] = {
                    'label': item.get('label', field_name),
                    'field_type': item_type or 'string',
                    'required': item.get('props', {}).get('required', False),
                    'sensitive': False,
                    'maskable': False,
                    'default_permission': 'write'
                }
        
        extract_fields(items)
        return field_metadata

    @staticmethod
    async def get_published_forms_simple(db: AsyncSession, application_id: str = None, all_apps: bool = False) -> List[Dict[str, Any]]:
        """
        获取已发布表单的简单列表（用于下拉选择）
        
        Args:
            application_id: 过滤指定应用，为 None 且 all_apps=False 时只返回无应用的表单
            all_apps: 为 True 时返回所有应用的已发布表单（移动端工作台使用）
        Returns:
            [{code, name, mainTable, application_id, application_name, fields: [{field, label, type}]}]
        """
        from core.application.model import Application

        conditions = [
            FormMeta.status == "published",
            FormMeta.is_deleted == False
        ]
        if application_id:
            conditions.append(FormMeta.application_id == application_id)
        elif not all_apps:
            conditions.append(FormMeta.application_id.is_(None))

        if all_apps:
            conditions.append(FormMeta.show_in_mobile == True)

        stmt = select(FormMeta, Application.name.label("application_name")).outerjoin(
            Application, Application.id == FormMeta.application_id
        ).where(
            *conditions
        ).order_by(FormMeta.name)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        simple_list = []
        for row in rows:
            form = row[0]
            application_name = row[1]
            # 提取表单字段信息
            fields = []
            form_config = form.form_config or {}
            items = form_config.get("items", [])
            
            def extract_fields(item_list: List[Dict], in_sub_table: bool = False):
                """递归提取字段"""
                for item in item_list:
                    item_type = item.get("type", "")
                    field = item.get("field", "")
                    label = item.get("label", "")
                    
                    # 跳过子表和布局组件
                    if item_type == "sub-table":
                        continue
                    
                    # 布局组件，递归处理
                    if item_type in ("grid", "tabs", "collapse", "steps"):
                        if item.get("columns"):
                            for col in item["columns"]:
                                extract_fields(col.get("children", []), in_sub_table)
                        if item.get("items"):
                            for sub_item in item["items"]:
                                extract_fields(sub_item.get("children", []), in_sub_table)
                        continue
                    
                    # 普通字段（排除非数据字段）
                    if field and not in_sub_table and item_type not in ("divider", "alert", "timeline", "text", "html", "spacer", "title"):
                        fields.append({
                            "field": field,
                            "label": label or field,
                            "type": item_type
                        })
            
            extract_fields(items)
            
            # 添加常用的系统字段到字段列表开头
            system_fields = [
                {"field": "id", "label": "ID", "type": "string"},
                {"field": "sys_create_datetime", "label": "创建时间", "type": "datetime"},
                {"field": "sys_update_datetime", "label": "更新时间", "type": "datetime"},
                {"field": "sys_creator_id", "label": "创建人ID", "type": "string"},
                {"field": "sys_modifier_id", "label": "修改人ID", "type": "string"},
                {"field": "sys_dept_id", "label": "部门ID", "type": "string"},
                {"field": "sort", "label": "排序", "type": "number"},
            ]
            # 将系统字段添加到开头
            fields = system_fields + fields
            
            simple_list.append({
                "code": form.code,
                "name": form.name,
                "mainTable": form.main_table,
                "application_id": form.application_id,
                "application_name": application_name,
                "icon": form.icon or "",
                "icon_bg_color": form.icon_bg_color or "",
                "form_type": form.form_type or "normal",
                "fields": fields
            })
        
        return simple_list

    @staticmethod
    async def register_published_forms_to_registry(db: AsyncSession):
        """
        启动时加载已发布的表单并注册资源类型到 ResourceRegistry
        用于数据权限和字段权限配置
        """
        from app.resource_registry import ResourceRegistry

        # 查询所有已发布的表单
        stmt = select(FormMeta).where(
            FormMeta.status == "published",
            FormMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        published_forms = result.scalars().all()

        for form in published_forms:
            resource_type = f"form:{form.code}"
            # 生成字段元数据
            field_metadata = FormService._generate_form_field_metadata(form)
            
            ResourceRegistry.register(
                resource_type=resource_type,
                service_class=None,
                display_name=form.name,
                application_id=form.application_id,
                field_metadata=field_metadata
            )
            logger.info(f"启动时注册表单资源类型: {resource_type}, application_id={form.application_id}, fields={len(field_metadata)}")
