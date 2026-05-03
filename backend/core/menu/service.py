#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Menu Service - 菜单服务层
"""
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from utils.redis import CacheManager
from core.menu.model import Menu
from core.menu.schema import MenuCreate, MenuUpdate

# 菜单缓存管理器
menu_cache = CacheManager(prefix="menu:")

# 缓存key
MENU_TREE_CACHE_KEY = "tree"
USER_ROUTE_CACHE_PREFIX = "user_route:"


class MenuService(BaseService[Menu, MenuCreate, MenuUpdate]):
    """
    菜单服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = Menu
    
    @classmethod
    async def get_by_name(cls, db: AsyncSession, name: str) -> Optional[Menu]:
        """根据菜单名称获取菜单"""
        result = await db.execute(
            select(Menu).where(
                Menu.name == name,
                Menu.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_path(cls, db: AsyncSession, path: str) -> Optional[Menu]:
        """根据路由路径获取菜单"""
        result = await db.execute(
            select(Menu).where(
                Menu.path == path,
                Menu.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def check_name_exists(
        cls,
        db: AsyncSession,
        name: str,
        exclude_id: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> bool:
        """检查菜单名称是否存在（在指定应用范围内）"""
        query = select(Menu).where(
            Menu.name == name,
            Menu.is_deleted == False  # noqa: E712
        )
        if exclude_id:
            query = query.where(Menu.id != exclude_id)
        if application_id:
            query = query.where(Menu.application_id == application_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    @classmethod
    async def check_path_exists(
        cls,
        db: AsyncSession,
        path: str,
        exclude_id: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> bool:
        """检查路由路径是否存在（在指定应用范围内）"""
        query = select(Menu).where(
            Menu.path == path,
            Menu.is_deleted == False  # noqa: E712
        )
        if exclude_id:
            query = query.where(Menu.id != exclude_id)
        if application_id:
            query = query.where(Menu.application_id == application_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    @classmethod
    async def get_children(cls, db: AsyncSession, parent_id: Optional[str]) -> List[Menu]:
        """获取直接子菜单"""
        if parent_id:
            query = select(Menu).where(
                Menu.parent_id == parent_id,
                Menu.is_deleted == False  # noqa: E712
            ).order_by(Menu.order)
        else:
            query = select(Menu).where(
                Menu.parent_id.is_(None),
                Menu.is_deleted == False  # noqa: E712
            ).order_by(Menu.order)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @classmethod
    async def get_child_count(cls, db: AsyncSession, menu_id: str) -> int:
        """获取直接子菜单数量"""
        result = await db.execute(
            select(func.count(Menu.id)).where(
                Menu.parent_id == menu_id,
                Menu.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar() or 0
    
    @classmethod
    async def get_level(cls, db: AsyncSession, menu: Menu) -> int:
        """计算菜单层级"""
        level = 0
        current = menu
        while current.parent_id:
            level += 1
            parent = await cls.get_by_id(db, current.parent_id)
            if not parent:
                break
            current = parent
        return level
    
    @classmethod
    async def get_ancestors(cls, db: AsyncSession, menu: Menu) -> List[Menu]:
        """获取所有祖先菜单"""
        ancestors = []
        current = menu
        while current.parent_id:
            parent = await cls.get_by_id(db, current.parent_id)
            if not parent:
                break
            ancestors.append(parent)
            current = parent
        return ancestors
    
    @classmethod
    async def get_descendants(cls, db: AsyncSession, menu_id: str) -> List[Menu]:
        """获取所有后代菜单"""
        descendants = []
        
        async def collect_children(parent_id: str):
            children = await cls.get_children(db, parent_id)
            for child in children:
                descendants.append(child)
                await collect_children(child.id)
        
        await collect_children(menu_id)
        return descendants
    
    @classmethod
    async def can_delete(cls, db: AsyncSession, menu_id: str) -> bool:
        """判断是否可以删除（没有子菜单）"""
        child_count = await cls.get_child_count(db, menu_id)
        return child_count == 0
    
    @classmethod
    async def _expand_menu_ids_with_parents(cls, db: AsyncSession, menu_ids: List[str]) -> List[str]:
        """
        扩展菜单ID列表，包含所有父级菜单ID
        确保菜单树的完整性
        """
        if not menu_ids:
            return []
        
        expanded_ids = set(menu_ids)
        
        # 获取所有指定的菜单
        result = await db.execute(
            select(Menu).where(
                Menu.id.in_(menu_ids),
                Menu.is_deleted == False  # noqa: E712
            )
        )
        menus = list(result.scalars().all())
        
        # 递归获取每个菜单的所有父级
        for menu in menus:
            ancestors = await cls.get_ancestors(db, menu)
            for ancestor in ancestors:
                expanded_ids.add(ancestor.id)
        
        return list(expanded_ids)
    
    @classmethod
    async def get_all_menus(
        cls, 
        db: AsyncSession, 
        application_id: Optional[str] = None,
        include_system: bool = True
    ) -> List[Menu]:
        """获取所有菜单（可按应用过滤）
        
        Args:
            db: 数据库会话
            application_id: 应用ID，用于过滤应用菜单
            include_system: 是否包含系统菜单，默认True
        """
        from sqlalchemy import or_
        
        if application_id:
            if include_system:
                # 如果指定了应用ID且包含系统菜单，返回系统菜单 + 该应用的菜单
                result = await db.execute(
                    select(Menu).where(
                        or_(
                            Menu.is_system == True,  # noqa: E712
                            Menu.application_id == application_id
                        ),
                        Menu.is_deleted == False  # noqa: E712
                    ).order_by(Menu.order)
                )
            else:
                # 如果指定了应用ID但不包含系统菜单，只返回该应用的菜单
                result = await db.execute(
                    select(Menu).where(
                        Menu.application_id == application_id,
                        Menu.is_deleted == False  # noqa: E712
                    ).order_by(Menu.order)
                )
        else:
            # 如果没有指定应用ID，返回系统菜单 + 主应用菜单
            result = await db.execute(
                select(Menu).where(
                    or_(
                        Menu.is_system == True,  # noqa: E712
                        Menu.application_id.is_(None)
                    ),
                    Menu.is_deleted == False  # noqa: E712
                ).order_by(Menu.order)
            )
        return list(result.scalars().all())
    
    @classmethod
    async def build_tree(
        cls, 
        db: AsyncSession, 
        application_id: Optional[str] = None,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """构建菜单树（可按应用过滤）"""
        menus = await cls.get_all_menus(db, application_id=application_id, include_system=include_system)
        
        # 构建菜单字典
        menu_dict = {}
        for menu in menus:
            child_count = await cls.get_child_count(db, menu.id)
            level = await cls.get_level(db, menu)
            menu_dict[menu.id] = {
                "id": menu.id,
                "parent_id": menu.parent_id,
                "application_id": menu.application_id,
                "is_system": menu.is_system,
                "name": menu.name,
                "title": menu.title,
                "authCode": menu.authCode,
                "path": menu.path,
                "type": menu.type,
                # 路由配置
                "component": menu.component,
                "redirect": menu.redirect,
                "activePath": menu.activePath,
                "query": menu.query,
                "noBasicLayout": menu.noBasicLayout,
                # 菜单展示
                "icon": menu.icon,
                "activeIcon": menu.activeIcon,
                "order": menu.order,
                "hideInMenu": menu.hideInMenu,
                "hideChildrenInMenu": menu.hideChildrenInMenu,
                "hideInBreadcrumb": menu.hideInBreadcrumb,
                # 标签页配置
                "hideInTab": menu.hideInTab,
                "affixTab": menu.affixTab,
                "affixTabOrder": menu.affixTabOrder,
                "keepAlive": menu.keepAlive,
                "maxNumOfOpenTab": menu.maxNumOfOpenTab,
                # 外部链接配置
                "link": menu.link,
                "iframeSrc": menu.iframeSrc,
                "openInNewWindow": menu.openInNewWindow,
                # 徽标配置
                "badge": menu.badge,
                "badgeType": menu.badgeType,
                "badgeVariants": menu.badgeVariants,
                # 计算字段
                "level": level,
                "childCount": child_count,
                "children": []
            }
        
        # 构建树形结构
        tree = []
        for menu_id, menu_data in menu_dict.items():
            parent_id = menu_data["parent_id"]
            if parent_id is None:
                tree.append(menu_data)
            elif parent_id in menu_dict:
                menu_dict[parent_id]["children"].append(menu_data)
        
        # 递归排序
        def sort_children(nodes):
            nodes.sort(key=lambda x: x["order"])
            for node in nodes:
                if node["children"]:
                    sort_children(node["children"])
        
        sort_children(tree)
        return tree
    
    @classmethod
    async def build_route_tree(
        cls, 
        menus: List[Menu], 
        app_code: Optional[str] = None, 
        dev_mode: bool = False,
        selected_menu_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        构建前端路由树
        
        Args:
            menus: 菜单列表
            app_code: 应用编码，如果提供则为所有路径添加前缀
            dev_mode: 开发模式
                - True: 使用 /app-dev/:appCode 前缀
                - False: 使用 /app/:appCode 前缀
            selected_menu_ids: 原始选中的菜单ID列表，用于过滤非选中的叶子菜单
        """
        # 构建菜单字典
        menu_dict = {}
        # 根据模式确定路径前缀
        path_prefix = "/app-dev" if dev_mode else "/app"
        
        for menu in menus:
            meta = {
                "title": menu.title or menu.name,
                "icon": menu.icon,
                "activeIcon": menu.activeIcon,
                "order": menu.order,
                "hideInMenu": menu.hideInMenu,
                "hideChildrenInMenu": menu.hideChildrenInMenu,
                "hideInBreadcrumb": menu.hideInBreadcrumb,
                "hideInTab": menu.hideInTab,
                "affixTab": menu.affixTab,
                "affixTabOrder": menu.affixTabOrder,
                "keepAlive": menu.keepAlive,
                "maxNumOfOpenTab": menu.maxNumOfOpenTab,
                "fullPathKey": menu.fullPathKey if hasattr(menu, 'fullPathKey') else True,
                "noBasicLayout": menu.noBasicLayout,
                "badge": menu.badge,
                "badgeType": menu.badgeType,
                "badgeVariants": menu.badgeVariants,
                "link": menu.link,
                "iframeSrc": menu.iframeSrc,
                "openInNewWindow": menu.openInNewWindow,
                "activePath": menu.activePath,
                "authCode": menu.authCode,
            }
            # 移除None值
            meta = {k: v for k, v in meta.items() if v is not None}
            
            # 如果是子应用，为所有菜单路径添加前缀（包括系统菜单）
            path = menu.path
            redirect = menu.redirect
            if app_code and path:
                # 为所有绝对路径添加前缀（以 / 开头的路径）
                if path.startswith('/'):
                    path = f"{path_prefix}/{app_code}{path}"
                if redirect and redirect.startswith('/'):
                    redirect = f"{path_prefix}/{app_code}{redirect}"

            menu_dict[menu.id] = {
                "name": menu.name,
                "path": path,
                "component": menu.component,
                "redirect": redirect,
                "meta": meta,
                "children": [],
                "_parent_id": menu.parent_id,
                "_order": menu.order,
            }

        # 构建树形结构
        tree = []
        for menu_id, menu_data in menu_dict.items():
            parent_id = menu_data.pop("_parent_id")
            if parent_id is None:
                tree.append(menu_data)
            elif parent_id in menu_dict:
                menu_dict[parent_id]["children"].append(menu_data)

        # 递归排序、过滤和清理
        def sort_filter_and_clean(nodes, selected_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
            """
            递归处理节点：排序、过滤非选中的叶子节点、清理空children
            返回过滤后的节点列表
            """
            nodes.sort(key=lambda x: x.pop("_order", 0))
            result = []
            for node in nodes:
                if node["children"]:
                    # 有子节点，递归处理
                    node["children"] = sort_filter_and_clean(node["children"], selected_ids)
                    # 如果子节点全被过滤掉了，检查当前节点是否在选中列表中
                    if node["children"]:
                        result.append(node)
                    elif selected_ids is None or node.get("_menu_id") in selected_ids:
                        node.pop("children", None)
                        result.append(node)
                else:
                    node.pop("children", None)
                    # 叶子节点：如果没有指定选中列表，或者在选中列表中，则保留
                    if selected_ids is None or node.get("_menu_id") in selected_ids:
                        result.append(node)
                # 清理临时字段
                node.pop("_menu_id", None)
            return result

        # 如果有选中列表，需要在menu_dict中保存menu_id用于过滤
        if selected_menu_ids:
            for menu_id, menu_data in menu_dict.items():
                menu_data["_menu_id"] = menu_id

        tree = sort_filter_and_clean(tree, selected_menu_ids)
        return tree
    
    @classmethod
    async def get_menu_tree_cached(
        cls, 
        db: AsyncSession, 
        application_id: Optional[str] = None,
        include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """获取菜单树（带缓存）"""
        # 根据 application_id 和 include_system 生成不同的缓存 key
        cache_key = MENU_TREE_CACHE_KEY
        if application_id:
            cache_key = f"{MENU_TREE_CACHE_KEY}:app:{application_id}"
            if not include_system:
                cache_key = f"{cache_key}:no_system"
        
        # 尝试从缓存获取
        cached = await menu_cache.get(cache_key)
        if cached:
            return cached
        
        # 从数据库构建
        tree = await cls.build_tree(db, application_id=application_id, include_system=include_system)
        
        # 缓存结果（1小时）
        await menu_cache.set(cache_key, tree, expire=3600)
        
        return tree
    
    @classmethod
    async def get_user_route_tree(
        cls,
        db: AsyncSession,
        user_id: str,
        is_superuser: bool = False,
        role_menu_ids: Optional[List[str]] = None,
        application_code: Optional[str] = None,
        dev_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取用户路由树
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            is_superuser: 是否超级管理员
            role_menu_ids: 角色关联的菜单ID列表
            application_code: 应用编码
            dev_mode: 开发模式
                - True: 只返回系统菜单（is_system=True），用于 /app-dev/{code}/ 路径
                - False: 只返回应用专属菜单（application_id=app.id），用于 /app/{code}/ 路径
        """
        # 如果指定了应用编码，缓存key包含应用编码和模式
        cache_key = f"{USER_ROUTE_CACHE_PREFIX}{user_id}"
        if application_code:
            mode_suffix = "dev" if dev_mode else "normal"
            cache_key = f"{cache_key}:app:{application_code}:{mode_suffix}"
        
        # 尝试从缓存获取
        cached = await menu_cache.get(cache_key)
        if cached:
            return cached
        
        # 获取菜单
        menus = []
        app = None  # 初始化app变量
        
        if application_code:
            # 子应用模式
            from core.application.model import Application
            app_result = await db.execute(
                select(Application).where(
                    Application.code == application_code,
                    Application.is_deleted == False  # noqa: E712
                )
            )
            app = app_result.scalar_one_or_none()
            
            if app:
                if dev_mode:
                    # 开发模式：只返回系统菜单
                    # 如果应用配置了 system_menu_ids，则只返回选中的系统菜单及其父级菜单
                    app_system_menu_ids = app.system_menu_ids if app.system_menu_ids else None
                    
                    if is_superuser:
                        if app_system_menu_ids:
                            # 有配置：获取选中的菜单及其所有父级菜单
                            expanded_menu_ids = await cls._expand_menu_ids_with_parents(db, app_system_menu_ids)
                            from sqlalchemy import and_
                            result = await db.execute(
                                select(Menu).where(
                                    and_(
                                        Menu.id.in_(expanded_menu_ids),
                                        Menu.is_system == True,  # noqa: E712
                                        Menu.is_deleted == False  # noqa: E712
                                    )
                                ).order_by(Menu.order)
                            )
                        else:
                            # 无配置：返回所有系统菜单
                            result = await db.execute(
                                select(Menu).where(
                                    Menu.is_system == True,  # noqa: E712
                                    Menu.is_deleted == False  # noqa: E712
                                ).order_by(Menu.order)
                            )
                        menus = list(result.scalars().all())
                    elif role_menu_ids:
                        from sqlalchemy import and_
                        # 取角色菜单和应用配置菜单的交集
                        effective_menu_ids = role_menu_ids
                        if app_system_menu_ids:
                            # 先扩展应用配置的菜单ID（包含父级）
                            expanded_app_menu_ids = await cls._expand_menu_ids_with_parents(db, app_system_menu_ids)
                            effective_menu_ids = list(set(role_menu_ids) & set(expanded_app_menu_ids))
                        
                        result = await db.execute(
                            select(Menu).where(
                                and_(
                                    Menu.id.in_(effective_menu_ids),
                                    Menu.is_system == True,  # noqa: E712
                                    Menu.is_deleted == False  # noqa: E712
                                )
                            ).order_by(Menu.order)
                        )
                        menus = list(result.scalars().all())
                else:
                    # 正常模式：只返回应用专属菜单（不包含系统菜单）
                    if is_superuser:
                        result = await db.execute(
                            select(Menu).where(
                                Menu.application_id == app.id,
                                Menu.is_deleted == False  # noqa: E712
                            ).order_by(Menu.order)
                        )
                        menus = list(result.scalars().all())
                    elif role_menu_ids:
                        from sqlalchemy import and_
                        result = await db.execute(
                            select(Menu).where(
                                and_(
                                    Menu.id.in_(role_menu_ids),
                                    Menu.application_id == app.id,
                                    Menu.is_deleted == False  # noqa: E712
                                )
                            ).order_by(Menu.order)
                        )
                        menus = list(result.scalars().all())
        else:
            # 主应用模式：获取系统菜单 + 无应用归属的菜单
            from sqlalchemy import or_
            if is_superuser:
                result = await db.execute(
                    select(Menu).where(
                        or_(
                            Menu.is_system == True,  # noqa: E712
                            Menu.application_id.is_(None)
                        ),
                        Menu.is_deleted == False  # noqa: E712
                    ).order_by(Menu.order)
                )
                menus = list(result.scalars().all())
            elif role_menu_ids:
                from sqlalchemy import and_
                result = await db.execute(
                    select(Menu).where(
                        and_(
                            Menu.id.in_(role_menu_ids),
                            or_(
                                Menu.is_system == True,  # noqa: E712
                                Menu.application_id.is_(None)
                            ),
                            Menu.is_deleted == False  # noqa: E712
                        )
                    ).order_by(Menu.order)
                )
                menus = list(result.scalars().all())
        
        # 构建路由树，传递 application_code 用于添加路径前缀
        # 开发模式使用 /app-dev/{code} 前缀，正常模式使用 /app/{code} 前缀
        # 如果是开发模式且有选中的系统菜单，传递选中列表用于过滤
        selected_ids = None
        if dev_mode and application_code and app and app.system_menu_ids:
            selected_ids = app.system_menu_ids
        tree = await cls.build_route_tree(menus, app_code=application_code, dev_mode=dev_mode, selected_menu_ids=selected_ids)
        
        # 缓存结果（5分钟，权限可能变更）
        await menu_cache.set(cache_key, tree, expire=300)
        
        return tree
    
    @classmethod
    async def invalidate_cache(cls):
        """清除菜单缓存（包括所有子应用的缓存）"""
        # 清除主应用菜单树缓存
        await menu_cache.delete(MENU_TREE_CACHE_KEY)
        # 清除所有子应用菜单树缓存
        await menu_cache.delete_pattern(f"{MENU_TREE_CACHE_KEY}:app:*")
        # 清除所有用户路由树缓存（包括主应用和子应用）
        await menu_cache.delete_pattern(f"{USER_ROUTE_CACHE_PREFIX}*")
    
    @classmethod
    async def invalidate_app_menu_cache(cls, app_code: str):
        """清除指定应用的菜单缓存"""
        # 清除该应用的菜单树缓存
        await menu_cache.delete_pattern(f"{MENU_TREE_CACHE_KEY}:app:{app_code}*")
        # 清除所有用户在该应用下的路由树缓存
        await menu_cache.delete_pattern(f"{USER_ROUTE_CACHE_PREFIX}*:app:{app_code}:*")
    
    @classmethod
    async def move_menu(
        cls,
        db: AsyncSession,
        menu_id: str,
        new_parent_id: Optional[str]
    ) -> Tuple[bool, str]:
        """
        移动菜单到新的父菜单下
        
        :return: (是否成功, 消息)
        """
        menu = await cls.get_by_id(db, menu_id)
        if not menu:
            return False, "菜单不存在"
        
        # 检查新父菜单
        if new_parent_id:
            if new_parent_id == menu_id:
                return False, "不能将自己设置为父菜单"
            
            new_parent = await cls.get_by_id(db, new_parent_id)
            if not new_parent:
                return False, "父菜单不存在"
            
            # 检查是否会形成循环引用
            ancestors = await cls.get_ancestors(db, new_parent)
            ancestor_ids = [a.id for a in ancestors]
            if menu.id in ancestor_ids or menu.id == new_parent.id:
                return False, "不能移动到自己或子菜单下"
        
        menu.parent_id = new_parent_id
        await db.commit()
        await cls.invalidate_cache()
        
        return True, "移动成功"
    
    @classmethod
    async def get_menu_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """获取菜单统计信息"""
        # 总数
        total_result = await db.execute(
            select(func.count(Menu.id)).where(Menu.is_deleted == False)  # noqa: E712
        )
        total_count = total_result.scalar() or 0
        
        # 按类型统计
        type_stats = {}
        type_choices = [
            ('catalog', '目录'),
            ('menu', '菜单'),
            ('external', '外部链接'),
            ('online_form', '在线表单'),
            ('online_page', '在线页面'),
            ('agent', '智能体'),
        ]
        for type_code, type_name in type_choices:
            count_result = await db.execute(
                select(func.count(Menu.id)).where(
                    Menu.type == type_code,
                    Menu.is_deleted == False  # noqa: E712
                )
            )
            type_stats[type_name] = count_result.scalar() or 0
        
        # 计算最大层级
        max_level = 0
        menus = await cls.get_all_menus(db)
        for menu in menus:
            level = await cls.get_level(db, menu)
            if level > max_level:
                max_level = level
        
        return {
            "totalCount": total_count,
            "typeStats": type_stats,
            "maxLevel": max_level,
        }
