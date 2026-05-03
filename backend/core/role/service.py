#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Role Service - 角色服务层
"""
from typing import Tuple, Dict, Any, Optional, List

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.base_service import BaseService
from core.role.model import Role
from core.role.schema import RoleCreate, RoleUpdate


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    """
    角色服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = Role
    
    @classmethod
    async def create(cls, db: AsyncSession, data: RoleCreate) -> Role:
        """创建角色，处理多对多关系"""
        role_data = data.model_dump(exclude={'menu_ids', 'permission_ids', 'dept_ids'})
        
        role = Role(**role_data)
        db.add(role)
        await db.flush()
        
        # 设置多对多关系
        if data.menu_ids:
            from core.menu.model import Menu
            result = await db.execute(select(Menu).where(Menu.id.in_(data.menu_ids)))
            menus = list(result.scalars().all())
            role.menus = menus
        
        if data.permission_ids:
            from core.permission.model import Permission
            result = await db.execute(select(Permission).where(Permission.id.in_(data.permission_ids)))
            permissions = list(result.scalars().all())
            role.permissions = permissions
        
        if data.dept_ids:
            from core.dept.model import Dept
            result = await db.execute(select(Dept).where(Dept.id.in_(data.dept_ids)))
            depts = list(result.scalars().all())
            role.depts = depts
        
        await db.commit()
        await db.refresh(role)
        return role
    
    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        record_id: str,
        data: RoleUpdate
    ) -> Optional[Role]:
        """更新角色，处理多对多关系"""
        role = await cls.get_by_id(db, record_id)
        if not role:
            return None
        
        update_data = data.model_dump(exclude_unset=True, exclude={'menu_ids', 'permission_ids', 'dept_ids'})
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        # 更新多对多关系
        menu_or_permission_updated = False
        
        if data.menu_ids is not None:
            from core.menu.model import Menu
            result = await db.execute(select(Menu).where(Menu.id.in_(data.menu_ids)))
            menus = list(result.scalars().all())
            role.menus = menus
            menu_or_permission_updated = True
        
        if data.permission_ids is not None:
            from core.permission.model import Permission
            result = await db.execute(select(Permission).where(Permission.id.in_(data.permission_ids)))
            permissions = list(result.scalars().all())
            role.permissions = permissions
            menu_or_permission_updated = True
        
        if data.dept_ids is not None:
            from core.dept.model import Dept
            result = await db.execute(select(Dept).where(Dept.id.in_(data.dept_ids)))
            depts = list(result.scalars().all())
            role.depts = depts
        
        await db.commit()
        await db.refresh(role)
        
        # 如果更新了菜单或权限，清除缓存
        if menu_or_permission_updated:
            await cls._invalidate_role_related_cache(record_id)
        
        return role
    
    @classmethod
    async def _invalidate_role_related_cache(cls, role_id: str):
        """
        清除角色相关的所有缓存，使权限变更立即生效
        
        1. 清除菜单路由缓存
        2. 清除 API 权限内存缓存（该角色）
        3. 清除所有用户的 Redis 用户信息缓存（因为不知道哪些用户拥有该角色）
        """
        # 1. 清除菜单路由缓存
        from core.menu.service import MenuService
        await MenuService.invalidate_cache()
        
        # 2. 清除该角色的 API 权限 Redis 缓存
        from utils.permission import clear_role_permission_cache
        await clear_role_permission_cache(role_id)
        
        # 3. 清除所有用户的 Redis 用户信息缓存
        from utils.user_info_cache import delete_all_cached_user_info
        await delete_all_cached_user_info()
    
    @classmethod
    async def get_by_id_with_relations(cls, db: AsyncSession, record_id: str) -> Optional[Role]:
        """获取角色详情（包含关联数据）"""
        result = await db.execute(
            select(Role)
            .options(
                selectinload(Role.menus),
                selectinload(Role.permissions),
                selectinload(Role.depts)
            )
            .where(Role.id == record_id, Role.is_deleted == False)  # noqa: E712
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_user_count(cls, db: AsyncSession, role_id: str) -> int:
        """获取角色下的用户数量"""
        from core.user.model import User
        result = await db.execute(
            select(func.count(User.id)).where(
                User.role_id == role_id,
                User.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar() or 0
    
    @classmethod
    async def can_delete(cls, db: AsyncSession, role_id: str) -> Tuple[bool, str]:
        """检查角色是否可以删除"""
        role = await cls.get_by_id(db, role_id)
        if not role:
            return False, "角色不存在"
        
        if role.is_system_role():
            return False, "系统角色不能删除"
        
        user_count = await cls.get_user_count(db, role_id)
        if user_count > 0:
            return False, f"该角色下还有 {user_count} 个用户，无法删除"
        
        return True, ""
    
    @classmethod
    async def batch_update_status(
        cls,
        db: AsyncSession,
        ids: List[str],
        status: bool
    ) -> int:
        """批量更新角色状态（系统角色不能禁用）"""
        count = 0
        for role_id in ids:
            role = await cls.get_by_id(db, role_id)
            if role and role.role_type == 1:  # 只更新自定义角色
                role.status = status
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
    ) -> Tuple[int, List[str]]:
        """批量删除角色"""
        success_count = 0
        failed_ids = []
        
        for role_id in ids:
            can_del, reason = await cls.can_delete(db, role_id)
            if can_del:
                if await cls.delete(db, role_id, hard=hard):
                    success_count += 1
                else:
                    failed_ids.append(role_id)
            else:
                failed_ids.append(role_id)
        
        return success_count, failed_ids
    
    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Role], int]:
        """搜索角色"""
        if not keyword:
            return [], 0
        
        search_filter = or_(
            Role.name.ilike(f"%{keyword}%"),
            Role.code.ilike(f"%{keyword}%"),
            Role.description.ilike(f"%{keyword}%")
        )
        
        count_result = await db.execute(
            select(func.count(Role.id)).where(
                search_filter,
                Role.is_deleted == False  # noqa: E712
            )
        )
        total = count_result.scalar() or 0
        
        result = await db.execute(
            select(Role).where(
                search_filter,
                Role.is_deleted == False  # noqa: E712
            )
            .order_by(Role.priority.desc(), Role.sys_update_datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        return items, total
    
    @classmethod
    async def get_all_active(cls, db: AsyncSession) -> List[Role]:
        """获取所有启用的角色"""
        result = await db.execute(
            select(Role).where(
                Role.status == True,  # noqa: E712
                Role.is_deleted == False  # noqa: E712
            ).order_by(Role.priority.desc(), Role.name)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_ids(cls, db: AsyncSession, ids: List[str]) -> List[Role]:
        """根据ID列表批量获取角色"""
        if not ids:
            return []
        
        result = await db.execute(
            select(Role).where(
                Role.id.in_(ids),
                Role.is_deleted == False  # noqa: E712
            )
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_role_users(
        cls,
        db: AsyncSession,
        role_id: str,
        page: int = 1,
        page_size: int = 20,
        username: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取角色下的用户列表（SQL 分页 + JOIN 部门）"""
        from core.dept.model import Dept
        from core.user.model import User
        from core.user.user_role_model import UserRole

        # 基础条件
        base_conditions = [
            UserRole.role_id == role_id,
            UserRole.is_deleted == False,  # noqa: E712
            User.user_status == 1,
            User.is_deleted == False,  # noqa: E712
        ]
        if username:
            base_conditions.append(
                or_(
                    User.username.ilike(f"%{username}%"),
                    User.name.ilike(f"%{username}%"),
                )
            )

        # count
        count_stmt = (
            select(func.count(User.id))
            .join(UserRole, UserRole.user_id == User.id)
            .where(*base_conditions)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        # 分页查询，LEFT JOIN Dept 一次拿到 dept_name
        query_stmt = (
            select(
                User.id,
                User.username,
                User.name,
                User.avatar,
                User.email,
                User.mobile,
                Dept.name.label("dept_name"),
            )
            .join(UserRole, UserRole.user_id == User.id)
            .outerjoin(Dept, and_(Dept.id == User.dept_id, Dept.is_deleted == False))  # noqa: E712
            .where(*base_conditions)
            .order_by(User.sys_create_datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await db.execute(query_stmt)).all()

        items = [
            {
                "id": row.id,
                "username": row.username,
                "name": row.name,
                "avatar": row.avatar,
                "email": row.email,
                "mobile": row.mobile,
                "dept_name": row.dept_name,
            }
            for row in rows
        ]
        return items, total
    
    @classmethod
    async def add_users_to_role(
        cls,
        db: AsyncSession,
        role_id: str,
        user_ids: List[str]
    ) -> int:
        """将用户添加到角色（通过多对多关联表）"""
        from core.user.user_role_model import UserRole

        added_count = 0
        for user_id in user_ids:
            # 检查是否已存在关联（包括软删除的）
            existing = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                )
            )
            record = existing.scalar_one_or_none()
            if record:
                # 如果是软删除的，恢复
                if record.is_deleted:
                    record.is_deleted = False
                    added_count += 1
            else:
                db.add(UserRole(user_id=user_id, role_id=role_id))
                added_count += 1

        if added_count > 0:
            await db.commit()

        return added_count

    @classmethod
    async def remove_users_from_role(
        cls,
        db: AsyncSession,
        role_id: str,
        user_ids: List[str]
    ) -> int:
        """从角色中移除用户（通过多对多关联表）"""
        from core.user.user_role_model import UserRole

        removed_count = 0
        for user_id in user_ids:
            result = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id,
                    UserRole.is_deleted == False,  # noqa: E712
                )
            )
            record = result.scalar_one_or_none()
            if record:
                record.is_deleted = True
                removed_count += 1

        if removed_count > 0:
            await db.commit()

        return removed_count
    
    @classmethod
    async def update_menus_permissions(
        cls,
        db: AsyncSession,
        role_id: str,
        menu_ids: List[str],
        permission_ids: List[str]
    ) -> bool:
        """更新角色的菜单和权限"""
        role = await cls.get_by_id_with_relations(db, role_id)
        if not role:
            return False
        
        # 更新菜单
        from core.menu.model import Menu
        result = await db.execute(select(Menu).where(Menu.id.in_(menu_ids)))
        menus = list(result.scalars().all())
        role.menus = menus
        
        # 更新权限
        from core.permission.model import Permission
        result = await db.execute(select(Permission).where(Permission.id.in_(permission_ids)))
        permissions = list(result.scalars().all())
        role.permissions = permissions
        
        await db.commit()
        
        # 清除缓存，确保权限变更立即生效
        await cls._invalidate_role_related_cache(role_id)
        
        return True
    
    @classmethod
    async def copy_role(
        cls,
        db: AsyncSession,
        source_role_id: str,
        new_name: str,
        new_code: str,
        creator_id: Optional[str] = None
    ) -> Optional[Role]:
        """复制角色"""
        source_role = await cls.get_by_id_with_relations(db, source_role_id)
        if not source_role:
            return None
        
        # 创建新角色
        new_role = Role(
            name=new_name,
            code=new_code,
            role_type=1,  # 复制的角色都是自定义角色
            status=source_role.status,
            data_scope=source_role.data_scope,
            priority=source_role.priority,
            description=source_role.description,
            remark=f"复制自角色: {source_role.name}",
            sys_creator_id=creator_id
        )
        db.add(new_role)
        await db.flush()
        
        # 复制关联关系
        new_role.menus = source_role.menus
        new_role.permissions = source_role.permissions
        new_role.depts = source_role.depts
        
        await db.commit()
        await db.refresh(new_role)
        return new_role
    
    @classmethod
    async def update_permissions(
        cls,
        db: AsyncSession,
        role_id: str,
        permission_ids: List[str]
    ) -> bool:
        """更新角色的权限"""
        role = await cls.get_by_id_with_relations(db, role_id)
        if not role:
            return False
        
        from core.permission.model import Permission
        result = await db.execute(select(Permission).where(Permission.id.in_(permission_ids)))
        permissions = list(result.scalars().all())
        role.permissions = permissions
        
        await db.commit()
        
        # 清除缓存，确保权限变更立即生效
        await cls._invalidate_role_related_cache(role_id)
        
        return True
    
    @classmethod
    async def get_menu_permission_tree(cls, db: AsyncSession, role: Role) -> Dict[str, Any]:
        """获取角色的菜单权限树"""
        from core.menu.model import Menu
        from core.permission.model import Permission
        
        # 获取所有菜单
        result = await db.execute(select(Menu).where(Menu.is_deleted == False))  # noqa: E712
        all_menus = list(result.scalars().all())
        
        # 获取该角色已分配的权限ID和菜单ID
        role_permission_ids = set(p.id for p in role.permissions) if role.permissions else set()
        role_menu_ids = set(m.id for m in role.menus) if role.menus else set()
        
        # 获取所有启用的权限
        result = await db.execute(
            select(Permission).where(Permission.is_active == True, Permission.is_deleted == False)  # noqa: E712
        )
        all_permissions = list(result.scalars().all())
        
        # 权限类型映射
        PERMISSION_TYPE_MAP = {
            0: '按钮权限',
            1: 'API权限',
            2: '数据权限',
            3: '其他权限',
        }
        
        # 按菜单分组权限
        permissions_by_menu = {}
        for perm in all_permissions:
            menu_id = perm.menu_id
            if menu_id not in permissions_by_menu:
                permissions_by_menu[menu_id] = []
            
            permission_type = perm.permission_type if perm.permission_type is not None else 3
            permission_type_display = PERMISSION_TYPE_MAP.get(permission_type, '其他权限')
            
            permissions_by_menu[menu_id].append({
                'id': perm.id,
                'label': perm.name,
                'name': perm.name,
                'code': perm.code,
                'permission_type': permission_type,
                'permission_type_display': permission_type_display,
                'checked': perm.id in role_permission_ids,
            })
        
        # 构建菜单树
        menu_map = {}
        root_menus = []
        
        for menu in all_menus:
            menu_node = {
                'id': menu.id,
                'label': menu.title or menu.name,
                'name': menu.name,
                'parent_id': menu.parent_id,
                'checked': menu.id in role_menu_ids,
                'children': [],
            }
            menu_map[menu.id] = menu_node
        
        # 建立父子关系
        for menu in all_menus:
            if menu.parent_id and menu.parent_id in menu_map:
                menu_map[menu.parent_id]['children'].append(menu_map[menu.id])
            else:
                root_menus.append(menu_map[menu.id])
        
        # 为叶子菜单添加权限
        for menu_id, menu_node in menu_map.items():
            if not menu_node['children']:
                menu_node['children'] = permissions_by_menu.get(menu_id, [])
        
        return {
            'menu_tree': root_menus,
            'permission_tree': [],
            'selected_menu_ids': list(role_menu_ids),
            'selected_permission_ids': list(role_permission_ids),
        }
    
    @classmethod
    async def get_role_menus(cls, db: AsyncSession, role: Role, application_id: Optional[str] = None) -> Dict[str, Any]:
        """获取角色的菜单列表
        
        Args:
            db: 数据库会话
            role: 角色对象
            application_id: 应用ID，如果指定则只返回该应用的菜单
        """
        from core.menu.model import Menu
        from core.permission.model import Permission
        
        # 获取该角色已选中的菜单ID
        role_menu_ids = set(m.id for m in role.menus) if role.menus else set()
        
        # 获取菜单，支持按应用过滤
        query = select(Menu).where(Menu.is_deleted == False)  # noqa: E712
        if application_id:
            query = query.where(Menu.application_id == application_id)
        result = await db.execute(query)
        all_menus = list(result.scalars().all())
        
        # 统计每个菜单的权限数量
        permission_counts = {}
        for menu in all_menus:
            count_result = await db.execute(
                select(func.count(Permission.id)).where(
                    Permission.menu_id == menu.id,
                    Permission.is_active == True,  # noqa: E712
                    Permission.is_deleted == False  # noqa: E712
                )
            )
            permission_counts[menu.id] = count_result.scalar() or 0
        
        # 构建菜单树
        menu_map = {}
        root_menus = []
        
        for menu in all_menus:
            menu_node = {
                'id': menu.id,
                'label': menu.title or menu.name,
                'name': menu.name,
                'parent_id': menu.parent_id,
                'application_id': menu.application_id,
                'checked': menu.id in role_menu_ids,
                'permission_count': permission_counts.get(menu.id, 0),
                'children': [],
            }
            menu_map[menu.id] = menu_node
            
            if not menu.parent_id:
                root_menus.append(menu_node)
        
        # 建立父子关系
        for menu_id, menu_node in menu_map.items():
            parent_id = menu_node['parent_id']
            if parent_id and parent_id in menu_map:
                menu_map[parent_id]['children'].append(menu_node)
        
        return {
            'menu_tree': root_menus,
            'selected_menu_ids': list(role_menu_ids),
        }
    
    @classmethod
    async def get_menu_permissions(cls, db: AsyncSession, role: Role, menu_id: str) -> Dict[str, Any]:
        """获取指定菜单的权限列表"""
        from core.permission.model import Permission
        
        # 获取该角色已选中的权限ID
        role_permission_ids = set(p.id for p in role.permissions) if role.permissions else set()
        
        # 权限类型映射
        PERMISSION_TYPE_MAP = {
            0: '按钮权限',
            1: 'API权限',
            2: '数据权限',
            3: '其他权限',
        }
        
        # 获取该菜单的所有权限
        result = await db.execute(
            select(Permission).where(
                Permission.menu_id == menu_id,
                Permission.is_active == True,  # noqa: E712
                Permission.is_deleted == False  # noqa: E712
            )
        )
        permissions = list(result.scalars().all())
        
        permission_list = []
        for perm in permissions:
            permission_type = perm.permission_type if perm.permission_type is not None else 3
            permission_type_display = PERMISSION_TYPE_MAP.get(permission_type, '其他权限')
            
            permission_list.append({
                'id': perm.id,
                'label': perm.name,
                'name': perm.name,
                'code': perm.code,
                'permission_type': permission_type,
                'permission_type_display': permission_type_display,
                'checked': perm.id in role_permission_ids,
            })
        
        return {
            'menu_id': menu_id,
            'permissions': permission_list,
        }
