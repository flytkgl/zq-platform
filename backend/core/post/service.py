#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post Service - 岗位服务层
"""
from io import BytesIO
from typing import Tuple, Dict, Any, Optional, List

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.post.model import Post
from core.post.schema import PostCreate, PostUpdate


class PostService(BaseService[Post, PostCreate, PostUpdate]):
    """
    岗位服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = Post
    
    # Excel导入导出配置
    excel_columns = {
        "name": "岗位名称",
        "code": "岗位编码",
        "post_type": "岗位类型",
        "post_level": "岗位级别",
        "status": "状态",
        "description": "描述",
    }
    excel_sheet_name = "岗位列表"
    
    @classmethod
    def _export_converter(cls, item: Any) -> Dict[str, Any]:
        """导出数据转换器"""
        return {
            "name": item.name,
            "code": item.code,
            "post_type": item.get_post_type_display(),
            "post_level": item.get_post_level_display(),
            "status": "启用" if item.status else "禁用",
            "description": item.description or "",
        }
    
    @classmethod
    def _import_processor(cls, row: Dict[str, Any]) -> Optional[Post]:
        """导入数据处理器"""
        name = row.get("name")
        code = row.get("code")
        if not name or not code:
            return None
        
        # 岗位类型映射
        type_map = {"管理岗": 0, "技术岗": 1, "业务岗": 2, "职能岗": 3, "其他": 4}
        post_type_str = row.get("post_type", "其他")
        post_type = type_map.get(post_type_str, 4)
        
        # 岗位级别映射
        level_map = {"高层": 0, "中层": 1, "基层": 2, "一般员工": 3}
        post_level_str = row.get("post_level", "一般员工")
        post_level = level_map.get(post_level_str, 3)
        
        status_str = row.get("status", "启用")
        status = status_str in ("启用", "true", "True", "1", True)
        
        return Post(
            name=str(name),
            code=str(code),
            post_type=post_type,
            post_level=post_level,
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
    async def get_user_count(cls, db: AsyncSession, post_id: str) -> int:
        """获取岗位下的用户数量"""
        from core.user.model import User
        result = await db.execute(
            select(func.count(User.id)).where(
                User.post_id == post_id,
                User.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar() or 0
    
    @classmethod
    async def can_delete(cls, db: AsyncSession, post_id: str) -> Tuple[bool, str]:
        """
        检查岗位是否可以删除
        
        :return: (是否可删除, 原因)
        """
        user_count = await cls.get_user_count(db, post_id)
        if user_count > 0:
            return False, f"该岗位下还有 {user_count} 个用户，无法删除"
        return True, ""
    
    @classmethod
    async def batch_update_status(
        cls,
        db: AsyncSession,
        ids: List[str],
        status: bool
    ) -> int:
        """
        批量更新岗位状态
        
        :return: 更新的记录数
        """
        count = 0
        for post_id in ids:
            post = await cls.get_by_id(db, post_id)
            if post:
                post.status = status
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
        批量删除岗位
        
        :return: (删除成功数, 删除失败的ID列表)
        """
        success_count = 0
        failed_ids = []
        
        for post_id in ids:
            can_del, reason = await cls.can_delete(db, post_id)
            if can_del:
                if await cls.delete(db, post_id, hard=hard):
                    success_count += 1
                else:
                    failed_ids.append(post_id)
            else:
                failed_ids.append(post_id)
        
        return success_count, failed_ids
    
    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Post], int]:
        """
        搜索岗位（模糊匹配名称、编码、描述）
        """
        if not keyword:
            return [], 0
        
        # 构建搜索条件
        search_filter = or_(
            Post.name.ilike(f"%{keyword}%"),
            Post.code.ilike(f"%{keyword}%"),
            Post.description.ilike(f"%{keyword}%")
        )
        
        # 查询总数
        count_result = await db.execute(
            select(func.count(Post.id)).where(
                search_filter,
                Post.is_deleted == False  # noqa: E712
            )
        )
        total = count_result.scalar() or 0
        
        # 查询数据
        result = await db.execute(
            select(Post).where(
                search_filter,
                Post.is_deleted == False  # noqa: E712
            )
            .order_by(Post.sys_create_datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        return items, total
    
    @classmethod
    async def search_with_data_scope(
        cls,
        db: AsyncSession,
        keyword: str,
        page: int,
        page_size: int
    ) -> Tuple[List[Post], int]:
        """
        搜索岗位（模糊匹配名称、编码、描述，自动应用数据权限过滤）
        
        自动从上下文获取当前用户信息和请求信息，无需手动传递任何参数
        """
        if not keyword:
            return [], 0
        
        from utils.permission import apply_data_scope_filter
        from utils.context import get_current_user_info_from_context
        
        # 从上下文获取用户信息和请求信息
        user_info = get_current_user_info_from_context()
        if not user_info:
            return [], 0
        
        # 获取数据权限过滤条件
        data_scope_filter = await apply_data_scope_filter(
            db=db,
            role_id=user_info.get("role_id"),
            is_superuser=user_info.get("is_superuser", False),
            user_id=user_info.get("user_id"),
            user_dept_id=user_info.get("dept_id"),
            request_path=user_info.get("request_path"),
            http_method=user_info.get("http_method")
        )
        
        # 构建搜索条件
        search_filter = or_(
            Post.name.ilike(f"%{keyword}%"),
            Post.code.ilike(f"%{keyword}%"),
            Post.description.ilike(f"%{keyword}%")
        )
        
        # 构建基础查询
        base_query = select(Post).where(
            search_filter,
            Post.is_deleted == False  # noqa: E712
        )
        
        # 应用数据权限过滤
        base_query = cls._apply_data_scope_to_query(
            query=base_query,
            data_scope_filter=data_scope_filter
        )
        
        # 查询总数
        count_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 查询数据
        result = await db.execute(
            base_query.order_by(Post.sys_create_datetime.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        return items, total
    
    @classmethod
    async def get_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """获取岗位统计信息"""
        # 总数
        total_result = await db.execute(
            select(func.count(Post.id)).where(Post.is_deleted == False)  # noqa: E712
        )
        total_count = total_result.scalar() or 0
        
        # 启用数
        active_result = await db.execute(
            select(func.count(Post.id)).where(
                Post.status == True,  # noqa: E712
                Post.is_deleted == False  # noqa: E712
            )
        )
        active_count = active_result.scalar() or 0
        
        # 按类型统计
        type_stats = {}
        for type_code, type_name in Post.POST_TYPE_CHOICES.items():
            count_result = await db.execute(
                select(func.count(Post.id)).where(
                    Post.post_type == type_code,
                    Post.is_deleted == False  # noqa: E712
                )
            )
            type_stats[type_name] = count_result.scalar() or 0
        
        # 按级别统计
        level_stats = {}
        for level_code, level_name in Post.POST_LEVEL_CHOICES.items():
            count_result = await db.execute(
                select(func.count(Post.id)).where(
                    Post.post_level == level_code,
                    Post.is_deleted == False  # noqa: E712
                )
            )
            level_stats[level_name] = count_result.scalar() or 0
        
        return {
            'total_count': total_count,
            'active_count': active_count,
            'inactive_count': total_count - active_count,
            'type_stats': type_stats,
            'level_stats': level_stats,
        }
    
    @classmethod
    async def get_by_dept(cls, db: AsyncSession, dept_id: str) -> List[Post]:
        """根据部门ID获取岗位列表"""
        result = await db.execute(
            select(Post).where(
                Post.dept_id == dept_id,
                Post.status == True,  # noqa: E712
                Post.is_deleted == False  # noqa: E712
            ).order_by(Post.post_level, Post.name)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_type(cls, db: AsyncSession, post_type: int) -> List[Post]:
        """根据岗位类型获取岗位列表"""
        result = await db.execute(
            select(Post).where(
                Post.post_type == post_type,
                Post.status == True,  # noqa: E712
                Post.is_deleted == False  # noqa: E712
            ).order_by(Post.post_level, Post.name)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_level(cls, db: AsyncSession, post_level: int) -> List[Post]:
        """根据岗位级别获取岗位列表"""
        result = await db.execute(
            select(Post).where(
                Post.post_level == post_level,
                Post.status == True,  # noqa: E712
                Post.is_deleted == False  # noqa: E712
            ).order_by(Post.name)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_ids(cls, db: AsyncSession, ids: List[str]) -> List[Post]:
        """根据ID列表批量获取岗位"""
        if not ids:
            return []
        
        result = await db.execute(
            select(Post).where(
                Post.id.in_(ids),
                Post.is_deleted == False  # noqa: E712
            )
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_post_users(cls, db: AsyncSession, post_id: str) -> List[Any]:
        """获取岗位下的用户列表"""
        from core.user.model import User
        
        result = await db.execute(
            select(User).where(
                User.post_id == post_id,
                User.user_status == 1,
                User.is_deleted == False  # noqa: E712
            )
        )
        return list(result.scalars().all())
    
    @classmethod
    async def add_users_to_post(
        cls,
        db: AsyncSession,
        post_id: str,
        user_ids: List[str]
    ) -> int:
        """将用户添加到岗位"""
        from core.user.model import User
        
        post = await cls.get_by_id(db, post_id)
        if not post:
            return 0
        
        added_count = 0
        for user_id in user_ids:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.post_id != post_id:
                user.post_id = post_id
                added_count += 1
        
        if added_count > 0:
            await db.commit()
        
        return added_count
    
    @classmethod
    async def remove_users_from_post(
        cls,
        db: AsyncSession,
        post_id: str,
        user_ids: List[str]
    ) -> int:
        """从岗位中移除用户"""
        from core.user.model import User
        
        removed_count = 0
        for user_id in user_ids:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.post_id == post_id:
                user.post_id = None
                removed_count += 1
        
        if removed_count > 0:
            await db.commit()
        
        return removed_count
    
    @classmethod
    async def get_all_simple(cls, db: AsyncSession) -> List[Post]:
        """获取所有启用的岗位（简化版，用于选择器）"""
        result = await db.execute(
            select(Post).where(
                Post.status == True,  # noqa: E712
                Post.is_deleted == False  # noqa: E712
            ).order_by(Post.post_level, Post.name)
        )
        return list(result.scalars().all())
