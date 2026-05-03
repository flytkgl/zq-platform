#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Permission Service - 权限服务层
"""
from typing import Tuple, Dict, Any, Optional, List

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.permission.model import Permission
from core.permission.schema import PermissionCreate, PermissionUpdate


class PermissionService(BaseService[Permission, PermissionCreate, PermissionUpdate]):
    """
    权限服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = Permission
    
    @classmethod
    async def check_code_unique(
        cls,
        db: AsyncSession,
        menu_id: str,
        code: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """
        检查同一菜单下权限编码是否唯一
        
        :return: True表示唯一，False表示已存在
        """
        query = select(Permission).where(
            Permission.menu_id == menu_id,
            Permission.code == code,
            Permission.is_deleted == False  # noqa: E712
        )
        if exclude_id:
            query = query.where(Permission.id != exclude_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is None
    
    @classmethod
    async def get_by_menu(cls, db: AsyncSession, menu_id: str) -> List[Permission]:
        """根据菜单ID获取权限列表"""
        result = await db.execute(
            select(Permission).where(
                Permission.menu_id == menu_id,
                Permission.is_active == True,  # noqa: E712
                Permission.is_deleted == False  # noqa: E712
            ).order_by(Permission.sort, Permission.sys_create_datetime)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_type(cls, db: AsyncSession, permission_type: int) -> List[Permission]:
        """根据权限类型获取权限列表"""
        result = await db.execute(
            select(Permission).where(
                Permission.permission_type == permission_type,
                Permission.is_active == True,  # noqa: E712
                Permission.is_deleted == False  # noqa: E712
            ).order_by(Permission.menu_id, Permission.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def batch_update_status(
        cls,
        db: AsyncSession,
        ids: List[str],
        is_active: bool
    ) -> int:
        """批量更新权限状态"""
        count = 0
        for perm_id in ids:
            perm = await cls.get_by_id(db, perm_id)
            if perm:
                perm.is_active = is_active
                count += 1
        
        if count > 0:
            await db.commit()
        
        return count
    
    @classmethod
    async def batch_delete(
        cls,
        db: AsyncSession,
        ids: List[str],
        hard: bool = False
    ) -> int:
        """批量删除权限"""
        count = 0
        for perm_id in ids:
            if await cls.delete(db, perm_id, hard=hard):
                count += 1
        return count
    
    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Permission], int]:
        """搜索权限"""
        if not keyword:
            return [], 0
        
        search_filter = or_(
            Permission.name.ilike(f"%{keyword}%"),
            Permission.code.ilike(f"%{keyword}%"),
            Permission.description.ilike(f"%{keyword}%")
        )
        
        count_result = await db.execute(
            select(func.count(Permission.id)).where(
                search_filter,
                Permission.is_deleted == False  # noqa: E712
            )
        )
        total = count_result.scalar() or 0
        
        result = await db.execute(
            select(Permission).where(
                search_filter,
                Permission.is_deleted == False  # noqa: E712
            )
            .order_by(Permission.sort, Permission.sys_create_datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        return items, total
    
    @classmethod
    async def get_all_active(cls, db: AsyncSession) -> List[Permission]:
        """获取所有启用的权限"""
        result = await db.execute(
            select(Permission).where(
                Permission.is_active == True,  # noqa: E712
                Permission.is_deleted == False  # noqa: E712
            ).order_by(Permission.menu_id, Permission.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_ids(cls, db: AsyncSession, ids: List[str]) -> List[Permission]:
        """根据ID列表批量获取权限"""
        if not ids:
            return []
        
        result = await db.execute(
            select(Permission).where(
                Permission.id.in_(ids),
                Permission.is_deleted == False  # noqa: E712
            )
        )
        return list(result.scalars().all())
    
    @classmethod
    def get_all_routes_from_app(cls, app) -> List[Dict[str, Any]]:
        """从FastAPI应用获取所有已注册的路由"""
        routes = []
        
        # HTTP方法映射
        METHOD_MAP = {
            'GET': 0,
            'POST': 1,
            'PUT': 2,
            'DELETE': 3,
            'PATCH': 4,
        }
        
        for route in app.routes:
            # 只处理APIRoute
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                path = route.path
                methods = route.methods or {'GET'}
                
                # 跳过文档路由
                if path in ['/docs', '/redoc', '/openapi.json']:
                    continue
                
                for method in methods:
                    if method in ['HEAD', 'OPTIONS']:
                        continue
                    
                    # 生成权限编码
                    # 将路径转换为编码格式: /api/core/user -> api:core:user
                    code_parts = [p for p in path.split('/') if p and not p.startswith('{')]
                    code = ':'.join(code_parts)
                    if not code:
                        code = 'root'
                    code = f"{code}:{method.lower()}"
                    
                    # 获取summary
                    summary = getattr(route, 'summary', None) or getattr(route, 'name', None) or ''
                    
                    routes.append({
                        'path': path,
                        'method': method,
                        'name': summary or f"{method} {path}",
                        'code': code,
                        'summary': summary,
                        'permission_type': 1,  # API权限
                        'http_method': METHOD_MAP.get(method, 0),
                        'is_active': True,
                    })
        
        return routes
    
    @classmethod
    async def batch_create_from_routes(
        cls,
        db: AsyncSession,
        menu_id: str,
        routes: List[Dict[str, Any]]
    ) -> Tuple[int, int, int, List[str]]:
        """
        从路由批量创建权限
        
        :return: (created, skipped, failed, errors)
        """
        created_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        
        for route in routes:
            try:
                # 检查权限是否已存在
                is_unique = await cls.check_code_unique(db, menu_id, route['code'])
                
                if not is_unique:
                    skipped_count += 1
                    continue
                
                # 创建权限
                permission = Permission(
                    menu_id=menu_id,
                    name=route['name'],
                    code=route['code'],
                    permission_type=route.get('permission_type', 1),
                    api_path=route['path'],
                    http_method=route.get('http_method', 0),
                    description=route.get('summary') or f"{route['name']}权限",
                    is_active=route.get('is_active', True),
                )
                db.add(permission)
                created_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"创建权限 {route.get('code', 'unknown')} 失败: {str(e)}")
        
        if created_count > 0:
            await db.commit()
        
        return created_count, skipped_count, failed_count, errors
    
    @classmethod
    async def auto_generate_permissions(
        cls,
        db: AsyncSession,
        app,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        自动扫描并生成权限
        
        :param dry_run: 如果为True，只预览不实际创建
        :return: 生成结果
        """
        from core.menu.model import Menu
        
        # 获取所有路由
        routes = cls.get_all_routes_from_app(app)
        
        if dry_run:
            return {
                'created': 0,
                'skipped': 0,
                'failed': 0,
                'permissions': routes,
                'dry_run': True,
            }
        
        # 按路径前缀分组，尝试匹配菜单
        created_total = 0
        skipped_total = 0
        failed_total = 0
        all_errors = []
        
        # 获取所有菜单
        result = await db.execute(select(Menu).where(Menu.is_deleted == False))  # noqa: E712
        all_menus = list(result.scalars().all())
        
        # 创建菜单路径映射
        menu_path_map = {}
        for menu in all_menus:
            if menu.path:
                # 标准化路径
                path = menu.path.strip('/')
                menu_path_map[path] = menu.id
        
        # 按路由路径匹配菜单
        routes_by_menu = {}
        unmatched_routes = []
        
        for route in routes:
            path = route['path'].strip('/')
            matched_menu_id = None
            
            # 尝试匹配菜单
            for menu_path, menu_id in menu_path_map.items():
                if path.startswith(menu_path) or menu_path in path:
                    matched_menu_id = menu_id
                    break
            
            if matched_menu_id:
                if matched_menu_id not in routes_by_menu:
                    routes_by_menu[matched_menu_id] = []
                routes_by_menu[matched_menu_id].append(route)
            else:
                unmatched_routes.append(route)
        
        # 为每个菜单创建权限
        for menu_id, menu_routes in routes_by_menu.items():
            created, skipped, failed, errors = await cls.batch_create_from_routes(
                db, menu_id, menu_routes
            )
            created_total += created
            skipped_total += skipped
            failed_total += failed
            all_errors.extend(errors)
        
        return {
            'created': created_total,
            'skipped': skipped_total,
            'failed': failed_total,
            'unmatched_routes': len(unmatched_routes),
            'errors': all_errors,
            'dry_run': False,
        }
