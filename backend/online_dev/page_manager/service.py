#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
页面元数据管理服务（异步版本）
"""
import logging
from typing import Any, Dict, List

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from online_dev.page_manager.model import PageMeta
from app.data_scope_utils import get_data_scope_filter, apply_data_scope_to_conditions

logger = logging.getLogger(__name__)

# 资源类型（用于数据权限配置）
RESOURCE_TYPE = "page"
RESOURCE_DISPLAY_NAME = "页面管理"


class PageServiceException(Exception):
    """页面服务异常"""
    pass


class PageService:
    """
    页面元数据管理服务
    
    数据权限：
    - 使用 list_with_data_scope() 自动应用数据权限
    - 支持本人、本部门、本部门及下级、全部等数据范围
    """

    # ============ 查询 ============

    @staticmethod
    async def list(
            db: AsyncSession,
            page: int = 1,
            page_size: int = 20,
            application_id: str = None,
            name: str = None,
            code: str = None,
            category: str = None,
            status: str = None
    ) -> Dict[str, Any]:
        """分页查询页面列表"""
        conditions = [PageMeta.is_deleted == False]

        # 应用过滤
        if application_id:
            conditions.append(PageMeta.application_id == application_id)
        else:
            # 如果没有指定 application_id，只返回主应用的页面（application_id 为 NULL）
            conditions.append(PageMeta.application_id.is_(None))

        if name:
            conditions.append(PageMeta.name.ilike(f"%{name}%"))
        if code:
            conditions.append(PageMeta.code.ilike(f"%{code}%"))
        if category:
            conditions.append(PageMeta.category == category)
        if status:
            conditions.append(PageMeta.status == status)

        # 获取总数
        count_stmt = select(func.count(PageMeta.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表
        offset = (page - 1) * page_size
        stmt = select(PageMeta).where(and_(*conditions)).order_by(
            PageMeta.sort, PageMeta.sys_create_datetime.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

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
            category: str = None,
            status: str = None
    ) -> Dict[str, Any]:
        """
        分页查询页面列表（带数据权限过滤）
        
        自动从上下文获取当前用户信息，应用数据权限过滤
        """
        conditions = [PageMeta.is_deleted == False]

        # 应用过滤
        if application_id:
            conditions.append(PageMeta.application_id == application_id)
        else:
            conditions.append(PageMeta.application_id.is_(None))

        if name:
            conditions.append(PageMeta.name.ilike(f"%{name}%"))
        if code:
            conditions.append(PageMeta.code.ilike(f"%{code}%"))
        if category:
            conditions.append(PageMeta.category == category)
        if status:
            conditions.append(PageMeta.status == status)

        # 获取数据权限过滤条件并应用
        data_scope_filter = await get_data_scope_filter(db, RESOURCE_TYPE)
        scope_conditions = apply_data_scope_to_conditions(PageMeta, data_scope_filter)
        conditions.extend(scope_conditions)

        # 获取总数
        count_stmt = select(func.count(PageMeta.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 获取列表
        offset = (page - 1) * page_size
        stmt = select(PageMeta).where(and_(*conditions)).order_by(
            PageMeta.sort, PageMeta.sys_create_datetime.desc()
        ).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    async def get(db: AsyncSession, page_id: str) -> PageMeta:
        """获取页面详情"""
        stmt = select(PageMeta).where(
            PageMeta.id == page_id,
            PageMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        page = result.scalar_one_or_none()

        if not page:
            raise PageServiceException(f"页面不存在: {page_id}")

        return page

    @staticmethod
    async def get_by_code(db: AsyncSession, code: str) -> PageMeta:
        """根据编码获取页面"""
        stmt = select(PageMeta).where(
            PageMeta.code == code,
            PageMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        page = result.scalar_one_or_none()

        if not page:
            raise PageServiceException(f"页面不存在: {code}")

        return page

    # ============ 创建 ============

    @staticmethod
    async def create(
            db: AsyncSession,
            data: Dict[str, Any],
            user_id: str = None
    ) -> PageMeta:
        """创建页面"""
        code = data.get("code")

        # 检查编码唯一性
        stmt = select(PageMeta).where(
            PageMeta.code == code,
            PageMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise PageServiceException(f"页面编码已存在: {code}")

        # 从上下文获取用户信息
        from utils.context import get_current_user_info_from_context
        user_info = get_current_user_info_from_context()
        
        page = PageMeta(
            application_id=data.get("application_id"),
            name=data.get("name"),
            code=code,
            category=data.get("category", ""),
            description=data.get("description", ""),
            page_config=data.get("page_config", {}),
            sort=data.get("sort", 0),
            sys_creator_id=user_id or (user_info.get('user_id') if user_info else None),
            sys_modifier_id=user_id or (user_info.get('user_id') if user_info else None),
        )
        
        # 自动填充部门ID
        if user_info and user_info.get('dept_id'):
            page.sys_dept_id = user_info.get('dept_id')
        
        db.add(page)
        await db.commit()
        await db.refresh(page)

        logger.info(f"页面创建成功: {page.code}")
        return page

    # ============ 更新 ============

    @staticmethod
    async def update(
            db: AsyncSession,
            page_id: str,
            data: Dict[str, Any],
            user_id: str = None
    ) -> PageMeta:
        """更新页面"""
        page = await PageService.get(db, page_id)

        # 更新基本字段
        if "name" in data and data["name"] is not None:
            page.name = data["name"]
        if "category" in data and data["category"] is not None:
            page.category = data["category"]
        if "description" in data and data["description"] is not None:
            page.description = data["description"]
        if "sort" in data and data["sort"] is not None:
            page.sort = data["sort"]
        if "page_config" in data and data["page_config"] is not None:
            page.page_config = data["page_config"]

        page.sys_modifier_id = user_id

        await db.commit()
        await db.refresh(page)

        logger.info(f"页面更新成功: {page.code}")
        return page

    # ============ 删除 ============

    @staticmethod
    async def delete(db: AsyncSession, page_id: str) -> bool:
        """删除页面（软删除）"""
        page = await PageService.get(db, page_id)

        page.is_deleted = True
        await db.commit()

        logger.info(f"页面删除成功: {page.code}")
        return True

    @staticmethod
    async def batch_delete(db: AsyncSession, page_ids: List[str]) -> int:
        """批量删除页面"""
        stmt = update(PageMeta).where(
            PageMeta.id.in_(page_ids),
            PageMeta.is_deleted == False
        ).values(is_deleted=True)
        result = await db.execute(stmt)
        await db.commit()

        count = result.rowcount
        logger.info(f"批量删除页面成功: {count} 个")
        return count

    # ============ 发布/取消发布 ============

    @staticmethod
    async def publish(
            db: AsyncSession,
            page_id: str,
            publish_config: Dict[str, Any] = None
    ) -> PageMeta:
        """发布页面并创建菜单"""
        from core.menu.model import Menu
        from core.menu.service import MenuService

        page = await PageService.get(db, page_id)

        if page.status == "published":
            raise PageServiceException("页面已发布")

        # 更新页面状态
        page.status = "published"
        page.version += 1

        # 创建或更新菜单
        if publish_config:
            menu_parent_id = publish_config.get("menu_parent_id")
            menu_path = f"/page-render/{page.code}"

            # 检查是否已存在该页面的菜单
            menu_stmt = select(Menu).where(
                Menu.path == menu_path
            )
            menu_result = await db.execute(menu_stmt)
            existing_menu = menu_result.scalar_one_or_none()

            if existing_menu:
                # 更新现有菜单
                existing_menu.name = publish_config.get("menu_name", page.name)
                existing_menu.title = publish_config.get("menu_name", page.name)
                existing_menu.parent_id = menu_parent_id
                existing_menu.icon = publish_config.get("menu_icon", "lucide:layout-dashboard")
                existing_menu.order = publish_config.get("menu_order", 0)
                existing_menu.type = "online_page"
                existing_menu.application_id = page.application_id
                logger.info(f"更新页面菜单: {page.code}")
            else:
                # 创建新菜单
                new_menu = Menu(
                    application_id=page.application_id,
                    name=publish_config.get("menu_name", page.name),
                    title=publish_config.get("menu_name", page.name),
                    path=menu_path,
                    component="online-dev/page-render/index",
                    type="online_page",
                    parent_id=menu_parent_id,
                    icon=publish_config.get("menu_icon", "lucide:layout-dashboard"),
                    order=publish_config.get("menu_order", 0),
                )
                db.add(new_menu)
                logger.info(f"创建页面菜单: {page.code}")

        await db.commit()
        await db.refresh(page)

        # 清空菜单缓存
        await MenuService.invalidate_cache()
        logger.info("已清空菜单缓存")

        logger.info(f"页面发布成功: {page.code}, version={page.version}")
        return page

    @staticmethod
    async def unpublish(db: AsyncSession, page_id: str) -> PageMeta:
        """取消发布页面并物理删除菜单"""
        from core.menu.model import Menu
        from core.menu.service import MenuService

        page = await PageService.get(db, page_id)

        if page.status == "draft":
            raise PageServiceException("页面未发布")

        page.status = "draft"

        # 物理删除对应菜单
        delete_menu_stmt = delete(Menu).where(
            Menu.path == f"/page-render/{page.code}"
        )
        result = await db.execute(delete_menu_stmt)

        if result.rowcount > 0:
            logger.info(f"物理删除页面菜单: {page.code}")

        await db.commit()
        await db.refresh(page)

        # 清空菜单缓存
        await MenuService.invalidate_cache()
        logger.info("已清空菜单缓存")

        logger.info(f"页面取消发布: {page.code}")
        return page

    # ============ 复制 ============

    @staticmethod
    async def copy(
            db: AsyncSession,
            page_id: str,
            new_code: str,
            new_name: str = None,
            user_id: str = None
    ) -> PageMeta:
        """复制页面"""
        source = await PageService.get(db, page_id)

        # 检查新编码唯一性
        stmt = select(PageMeta).where(
            PageMeta.code == new_code,
            PageMeta.is_deleted == False
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise PageServiceException(f"页面编码已存在: {new_code}")

        new_page = PageMeta(
            name=new_name or f"{source.name}_副本",
            code=new_code,
            category=source.category,
            description=source.description,
            status="draft",
            version=1,
            page_config=source.page_config,
            sort=source.sort,
            sys_creator_id=user_id,
            sys_modifier_id=user_id,
        )
        db.add(new_page)
        await db.commit()
        await db.refresh(new_page)

        logger.info(f"页面复制成功: {source.code} -> {new_code}")
        return new_page

    # ============ 导入/导出 ============

    @staticmethod
    async def export_config(db: AsyncSession, page_id: str) -> Dict[str, Any]:
        """导出页面配置"""
        page = await PageService.get(db, page_id)

        return {
            "name": page.name,
            "code": page.code,
            "category": page.category,
            "description": page.description,
            "page_config": page.page_config,
        }

    @staticmethod
    async def import_config(
            db: AsyncSession,
            data: Dict[str, Any],
            user_id: str = None
    ) -> PageMeta:
        """导入页面配置"""
        required_fields = ["name", "code"]
        for field in required_fields:
            if not data.get(field):
                raise PageServiceException(f"缺少必要字段: {field}")

        return await PageService.create(db, data, user_id)

    # ============ 获取分类列表 ============

    @staticmethod
    async def get_categories(db: AsyncSession) -> List[str]:
        """获取所有分类"""
        stmt = select(PageMeta.category).where(
            PageMeta.is_deleted == False,
            PageMeta.category != ""
        ).distinct()

        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]
