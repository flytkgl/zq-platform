#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dept Service - 部门服务层
"""
from io import BytesIO
from typing import Tuple, Dict, Any, Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.base_service import BaseService
from core.dept.model import Dept
from core.dept.schema import DeptCreate, DeptUpdate, DeptTreeNode


class DeptService(BaseService[Dept, DeptCreate, DeptUpdate]):
    """
    部门服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = Dept
    
    # Excel导入导出配置
    excel_columns = {
        "name": "部门名称",
        "code": "部门编码",
        "dept_type": "部门类型",
        "phone": "部门电话",
        "email": "部门邮箱",
        "status": "状态",
        "description": "描述",
    }
    excel_sheet_name = "部门列表"
    
    @classmethod
    def _export_converter(cls, item: Any) -> Dict[str, Any]:
        """导出数据转换器"""
        return {
            "name": item.name,
            "code": item.code or "",
            "dept_type": item.get_dept_type_display(),
            "phone": item.phone or "",
            "email": item.email or "",
            "status": "启用" if item.status else "禁用",
            "description": item.description or "",
        }
    
    @classmethod
    def _import_processor(cls, row: Dict[str, Any]) -> Optional[Dept]:
        """导入数据处理器"""
        name = row.get("name")
        if not name:
            return None
        
        # 部门类型映射
        type_map = {"公司": "company", "部门": "department", "小组": "team", "其他": "other"}
        dept_type_str = row.get("dept_type", "部门")
        dept_type = type_map.get(dept_type_str, "department")
        
        status_str = row.get("status", "启用")
        status = status_str in ("启用", "true", "True", "1", True)
        
        return Dept(
            name=str(name),
            code=str(row.get("code") or "") or None,
            dept_type=dept_type,
            phone=str(row.get("phone") or "") or None,
            email=str(row.get("email") or "") or None,
            status=status,
            description=str(row.get("description") or "") or None,
        )
    
    @classmethod
    async def export_to_excel(
        cls,
        db: AsyncSession,
        data_converter: Any = None
    ) -> BytesIO:
        """导出到Excel"""
        return await super().export_to_excel(db, cls._export_converter)
    
    @classmethod
    async def import_from_excel(
        cls,
        db: AsyncSession,
        file_content: bytes,
        row_processor: Any = None
    ) -> Tuple[int, int]:
        """从Excel导入"""
        return await super().import_from_excel(db, file_content, cls._import_processor)
    
    @classmethod
    async def create(cls, db: AsyncSession, data: DeptCreate) -> Dept:
        """
        创建部门，自动计算层级和路径
        """
        dept_data = data.model_dump()
        
        # 计算层级和路径
        parent_id = dept_data.get("parent_id")
        if parent_id:
            parent = await cls.get_by_id(db, parent_id)
            if parent:
                dept_data["level"] = parent.level + 1
                dept_data["path"] = f"{parent.path or '/'}{parent.id}/"
            else:
                dept_data["level"] = 0
                dept_data["path"] = "/"
        else:
            dept_data["level"] = 0
            dept_data["path"] = "/"
        
        db_obj = Dept(**dept_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        record_id: str,
        data: DeptUpdate
    ) -> Optional[Dept]:
        """
        更新部门，如果父部门变化则重新计算层级和路径
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 如果父部门变化，重新计算层级和路径
        if "parent_id" in update_data:
            parent_id = update_data["parent_id"]
            if parent_id:
                parent = await cls.get_by_id(db, parent_id)
                if parent:
                    update_data["level"] = parent.level + 1
                    update_data["path"] = f"{parent.path or '/'}{parent.id}/"
                else:
                    update_data["level"] = 0
                    update_data["path"] = "/"
            else:
                update_data["level"] = 0
                update_data["path"] = "/"
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    @classmethod
    async def get_tree(cls, db: AsyncSession, parent_id: Optional[str] = None) -> List[DeptTreeNode]:
        """
        获取部门树形结构
        
        :param db: 数据库会话
        :param parent_id: 父部门ID，None表示获取所有顶级部门
        :return: 部门树形列表
        """
        # 获取所有未删除的部门
        result = await db.execute(
            select(Dept)
            .where(Dept.is_deleted == False)  # noqa: E712
            .order_by(Dept.sort.desc(), Dept.sys_create_datetime)
        )
        all_depts = result.scalars().all()
        
        # 构建部门字典
        dept_dict = {dept.id: dept for dept in all_depts}
        
        # 构建树形结构
        def build_tree(parent_id: Optional[str]) -> List[DeptTreeNode]:
            children = []
            for dept in all_depts:
                if dept.parent_id == parent_id:
                    node = DeptTreeNode(
                        id=dept.id,
                        name=dept.name,
                        code=dept.code,
                        parent_id=dept.parent_id,
                        dept_type=dept.dept_type,
                        status=dept.status,
                        level=dept.level,
                        sort=dept.sort,
                        children=build_tree(dept.id)
                    )
                    children.append(node)
            return children
        
        return build_tree(parent_id)
    
    @classmethod
    async def get_children(cls, db: AsyncSession, parent_id: str) -> List[Dept]:
        """
        获取直接子部门列表
        """
        result = await db.execute(
            select(Dept)
            .where(
                Dept.parent_id == parent_id,
                Dept.is_deleted == False  # noqa: E712
            )
            .order_by(Dept.sort.desc(), Dept.sys_create_datetime)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_descendants(cls, db: AsyncSession, dept_id: str) -> List[Dept]:
        """
        获取所有后代部门（通过path字段查询）
        """
        dept = await cls.get_by_id(db, dept_id)
        if not dept:
            return []
        
        # 使用path字段进行模糊查询
        search_path = f"{dept.path or '/'}{dept.id}/"
        result = await db.execute(
            select(Dept)
            .where(
                Dept.path.like(f"{search_path}%"),
                Dept.is_deleted == False  # noqa: E712
            )
            .order_by(Dept.level, Dept.sort.desc())
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_ancestors(cls, db: AsyncSession, dept_id: str) -> List[Dept]:
        """
        获取所有祖先部门
        """
        ancestors = []
        current = await cls.get_by_id(db, dept_id)
        
        while current and current.parent_id:
            parent = await cls.get_by_id(db, current.parent_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    @classmethod
    async def can_delete(cls, db: AsyncSession, dept_id: str) -> Tuple[bool, str]:
        """
        检查部门是否可以删除
        
        :return: (是否可删除, 原因)
        """
        # 检查是否有子部门
        children = await cls.get_children(db, dept_id)
        if children:
            return False, "该部门下存在子部门，无法删除"
        
        # 检查是否有用户（需要导入User模型后才能检查）
        # 这里暂时返回True，后续可以添加用户检查
        return True, ""
    
    @classmethod
    async def batch_update_status(
        cls,
        db: AsyncSession,
        ids: List[str],
        status: bool
    ) -> int:
        """
        批量更新部门状态
        
        :return: 更新的记录数
        """
        count = 0
        for dept_id in ids:
            dept = await cls.get_by_id(db, dept_id)
            if dept:
                dept.status = status
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
        """
        批量删除部门
        
        :return: (删除成功数, 删除失败的ID列表)
        """
        success_count = 0
        failed_ids = []
        
        for dept_id in ids:
            can_del, reason = await cls.can_delete(db, dept_id)
            if can_del:
                if await cls.delete(db, dept_id, hard=hard):
                    success_count += 1
                else:
                    failed_ids.append(dept_id)
            else:
                failed_ids.append(dept_id)
        
        return success_count, failed_ids
    
    @classmethod
    async def get_user_count(cls, db: AsyncSession, dept_id: str) -> int:
        """获取部门下的用户数量"""
        from core.user.model import User
        result = await db.execute(
            select(func.count(User.id)).where(
                User.dept_id == dept_id,
                User.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar() or 0
    
    @classmethod
    async def get_child_count(cls, db: AsyncSession, dept_id: str) -> int:
        """获取直接子部门数量"""
        result = await db.execute(
            select(func.count(Dept.id)).where(
                Dept.parent_id == dept_id,
                Dept.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar() or 0
    
    @classmethod
    async def search(cls, db: AsyncSession, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索部门（模糊匹配部门名称或编码）
        返回匹配部门及其完整的层级路径
        """
        if not keyword:
            return []
        
        # 搜索部门
        result = await db.execute(
            select(Dept).where(
                (Dept.name.ilike(f"%{keyword}%") | Dept.code.ilike(f"%{keyword}%")),
                Dept.is_deleted == False  # noqa: E712
            )
        )
        matched_depts = list(result.scalars().all())
        
        # 收集所有需要的部门ID（包括匹配部门和其所有祖先）
        dept_ids_to_include = set()
        for dept in matched_depts:
            dept_ids_to_include.add(dept.id)
            ancestors = await cls.get_ancestors(db, dept.id)
            for ancestor in ancestors:
                dept_ids_to_include.add(ancestor.id)
        
        # 获取所有需要的部门
        result = await db.execute(
            select(Dept).where(
                Dept.id.in_(dept_ids_to_include),
                Dept.is_deleted == False  # noqa: E712
            )
        )
        all_depts = list(result.scalars().all())
        
        # 构建部门字典
        dept_dict_map = {}
        for dept in all_depts:
            child_count = await cls.get_child_count(db, dept.id)
            user_count = await cls.get_user_count(db, dept.id)
            dept_dict = {
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'dept_type': dept.dept_type,
                'dept_type_display': dept.get_dept_type_display(),
                'status': dept.status,
                'level': dept.level,
                'path': dept.path,
                'parent_id': dept.parent_id,
                'lead_id': dept.lead_id,
                'phone': dept.phone,
                'email': dept.email,
                'description': dept.description,
                'sort': dept.sort,
                'child_count': child_count,
                'user_count': user_count,
            }
            dept_dict_map[dept.id] = dept_dict
        
        # 构建树形结构
        roots = []
        for dept_id, dept in dept_dict_map.items():
            parent_id = dept['parent_id']
            if parent_id is None:
                roots.append(dept)
            elif parent_id in dept_dict_map:
                parent = dept_dict_map[parent_id]
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(dept)
        
        return roots
    
    @classmethod
    async def get_by_ids(cls, db: AsyncSession, ids: List[str]) -> List[Dict[str, Any]]:
        """
        根据ID列表批量获取部门信息（包含完整的层级路径）
        """
        if not ids:
            return []
        
        # 收集所有需要的部门ID
        dept_ids_to_include = set()
        result = await db.execute(
            select(Dept).where(
                Dept.id.in_(ids),
                Dept.is_deleted == False  # noqa: E712
            )
        )
        target_depts = list(result.scalars().all())
        
        for dept in target_depts:
            dept_ids_to_include.add(dept.id)
            ancestors = await cls.get_ancestors(db, dept.id)
            for ancestor in ancestors:
                dept_ids_to_include.add(ancestor.id)
        
        # 获取所有需要的部门
        result = await db.execute(
            select(Dept).where(
                Dept.id.in_(dept_ids_to_include),
                Dept.is_deleted == False  # noqa: E712
            )
        )
        all_depts = list(result.scalars().all())
        
        # 构建字典和树形结构
        dept_dict_map = {}
        for dept in all_depts:
            child_count = await cls.get_child_count(db, dept.id)
            user_count = await cls.get_user_count(db, dept.id)
            dept_dict = {
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'dept_type': dept.dept_type,
                'status': dept.status,
                'level': dept.level,
                'parent_id': dept.parent_id,
                'child_count': child_count,
                'user_count': user_count,
            }
            dept_dict_map[dept.id] = dept_dict
        
        roots = []
        for dept_id, dept in dept_dict_map.items():
            parent_id = dept['parent_id']
            if parent_id is None:
                roots.append(dept)
            elif parent_id in dept_dict_map:
                parent = dept_dict_map[parent_id]
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(dept)
        
        return roots
    
    @classmethod
    async def get_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """获取部门统计信息"""
        # 总数
        total_result = await db.execute(
            select(func.count(Dept.id)).where(Dept.is_deleted == False)  # noqa: E712
        )
        total_count = total_result.scalar() or 0
        
        # 启用数
        active_result = await db.execute(
            select(func.count(Dept.id)).where(
                Dept.status == True,  # noqa: E712
                Dept.is_deleted == False  # noqa: E712
            )
        )
        active_count = active_result.scalar() or 0
        
        # 根部门数
        root_result = await db.execute(
            select(func.count(Dept.id)).where(
                Dept.parent_id.is_(None),
                Dept.is_deleted == False  # noqa: E712
            )
        )
        root_count = root_result.scalar() or 0
        
        # 按类型统计
        type_stats = {}
        type_choices = [
            ('company', '公司'),
            ('department', '部门'),
            ('team', '小组'),
            ('other', '其他'),
        ]
        for type_code, type_name in type_choices:
            count_result = await db.execute(
                select(func.count(Dept.id)).where(
                    Dept.dept_type == type_code,
                    Dept.is_deleted == False  # noqa: E712
                )
            )
            type_stats[type_name] = count_result.scalar() or 0
        
        # 最大层级
        max_level_result = await db.execute(
            select(func.max(Dept.level)).where(Dept.is_deleted == False)  # noqa: E712
        )
        max_level = max_level_result.scalar() or 0
        
        return {
            'total_count': total_count,
            'active_count': active_count,
            'inactive_count': total_count - active_count,
            'root_count': root_count,
            'type_stats': type_stats,
            'max_level': max_level,
        }
    
    @classmethod
    async def move(
        cls,
        db: AsyncSession,
        dept_id: str,
        new_parent_id: Optional[str]
    ) -> Tuple[bool, str]:
        """
        移动部门到新的父部门下
        
        :return: (是否成功, 消息)
        """
        dept = await cls.get_by_id(db, dept_id)
        if not dept:
            return False, "部门不存在"
        
        # 检查新父部门
        if new_parent_id:
            if new_parent_id == dept_id:
                return False, "不能将自己设置为父部门"
            
            new_parent = await cls.get_by_id(db, new_parent_id)
            if not new_parent:
                return False, "父部门不存在"
            
            # 检查是否会形成循环引用
            ancestors = await cls.get_ancestors(db, new_parent_id)
            ancestor_ids = [a.id for a in ancestors]
            if dept.id in ancestor_ids or dept.id == new_parent.id:
                return False, "不能移动到自己或子部门下"
            
            dept.parent_id = new_parent_id
            dept.level = new_parent.level + 1
            dept.path = f"{new_parent.path or '/'}{new_parent.id}/"
        else:
            dept.parent_id = None
            dept.level = 0
            dept.path = "/"
        
        await db.commit()
        return True, "移动成功"
    
    @classmethod
    async def get_dept_users(
        cls,
        db: AsyncSession,
        dept_id: str,
        include_children: bool = False
    ) -> List[Any]:
        """获取部门下的用户列表"""
        from core.user.model import User
        
        if include_children:
            # 获取部门及其所有子部门的用户
            descendants = await cls.get_descendants(db, dept_id)
            dept_ids = [dept_id] + [d.id for d in descendants]
            result = await db.execute(
                select(User).where(
                    User.dept_id.in_(dept_ids),
                    User.user_status == 1,
                    User.is_deleted == False  # noqa: E712
                )
            )
        else:
            # 只获取当前部门的用户
            result = await db.execute(
                select(User).where(
                    User.dept_id == dept_id,
                    User.user_status == 1,
                    User.is_deleted == False  # noqa: E712
                )
            )
        
        return list(result.scalars().all())
    
    @classmethod
    async def add_users_to_dept(
        cls,
        db: AsyncSession,
        dept_id: str,
        user_ids: List[str]
    ) -> int:
        """将用户添加到部门"""
        from core.user.model import User
        
        dept = await cls.get_by_id(db, dept_id)
        if not dept:
            return 0
        
        added_count = 0
        for user_id in user_ids:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.dept_id != dept_id:
                user.dept_id = dept_id
                added_count += 1
        
        if added_count > 0:
            await db.commit()
        
        return added_count
    
    @classmethod
    async def remove_users_from_dept(
        cls,
        db: AsyncSession,
        dept_id: str,
        user_ids: List[str]
    ) -> int:
        """从部门中移除用户"""
        from core.user.model import User
        
        removed_count = 0
        for user_id in user_ids:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.dept_id == dept_id:
                user.dept_id = None
                removed_count += 1
        
        if removed_count > 0:
            await db.commit()
        
        return removed_count
    
    @classmethod
    async def get_by_parent(cls, db: AsyncSession, parent_id: Optional[str]) -> List[Dict[str, Any]]:
        """根据父部门ID获取直接子部门"""
        if parent_id:
            query = select(Dept).where(
                Dept.parent_id == parent_id,
                Dept.is_deleted == False  # noqa: E712
            ).order_by(Dept.sort.desc())
        else:
            query = select(Dept).where(
                Dept.parent_id.is_(None),
                Dept.is_deleted == False  # noqa: E712
            ).order_by(Dept.sort.desc())
        
        result = await db.execute(query)
        depts = list(result.scalars().all())
        
        dept_list = []
        for dept in depts:
            child_count = await cls.get_child_count(db, dept.id)
            user_count = await cls.get_user_count(db, dept.id)
            dept_dict = {
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'dept_type': dept.dept_type,
                'dept_type_display': dept.get_dept_type_display(),
                'status': dept.status,
                'level': dept.level,
                'path': dept.path,
                'parent_id': dept.parent_id,
                'lead_id': dept.lead_id,
                'phone': dept.phone,
                'email': dept.email,
                'description': dept.description,
                'sort': dept.sort,
                'child_count': child_count,
                'user_count': user_count,
            }
            dept_list.append(dept_dict)
        
        return dept_list
