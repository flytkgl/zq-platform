#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用管理服务层
"""
from typing import Optional, List, Tuple, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.application.model import Application
from core.application.schema import ApplicationCreate, ApplicationUpdate


class ApplicationService(BaseService[Application, ApplicationCreate, ApplicationUpdate]):
    """
    应用服务层
    继承BaseService，自动获得增删改查功能
    """

    model = Application

    # Excel导入导出配置
    excel_columns = {
        "name": "应用名称",
        "code": "应用编码",
        "description": "描述",
        "app_type": "应用类型",
        "status": "状态",
    }
    excel_sheet_name = "应用列表"

    @classmethod
    async def get_by_code(
        cls,
        db: AsyncSession,
        code: str
    ) -> Optional[Application]:
        """
        根据应用编码获取应用
        
        :param db: 数据库会话
        :param code: 应用编码
        :return: 应用或None
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.code == code,
                cls.model.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_list_by_owner(
        cls,
        db: AsyncSession,
        owner_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Application], int]:
        """
        获取指定用户拥有的应用列表
        
        :param db: 数据库会话
        :param owner_id: 所有者ID
        :param page: 页码
        :param page_size: 每页数量
        :return: (应用列表, 总数)
        """
        filters = [cls.model.owner_id == owner_id]
        return await cls.get_list(db, page, page_size, filters)

    @classmethod
    async def get_list_by_status(
        cls,
        db: AsyncSession,
        status: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Application], int]:
        """
        根据状态获取应用列表
        
        :param db: 数据库会话
        :param status: 状态
        :param page: 页码
        :param page_size: 每页数量
        :return: (应用列表, 总数)
        """
        filters = [cls.model.status == status]
        return await cls.get_list(db, page, page_size, filters)

    @classmethod
    async def get_list_by_type(
        cls,
        db: AsyncSession,
        app_type: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Application], int]:
        """
        根据类型获取应用列表
        
        :param db: 数据库会话
        :param app_type: 应用类型
        :param page: 页码
        :param page_size: 每页数量
        :return: (应用列表, 总数)
        """
        filters = [cls.model.app_type == app_type]
        return await cls.get_list(db, page, page_size, filters)

    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        keyword: Optional[str] = None,
        app_type: Optional[str] = None,
        status: Optional[str] = None,
        owner_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Application], int]:
        """
        搜索应用
        
        :param db: 数据库会话
        :param keyword: 关键词（搜索名称和描述）
        :param app_type: 应用类型
        :param status: 状态
        :param owner_id: 所有者ID
        :param page: 页码
        :param page_size: 每页数量
        :return: (应用列表, 总数)
        """
        filters = []
        
        if keyword:
            filters.append(
                (cls.model.name.ilike(f"%{keyword}%")) | 
                (cls.model.description.ilike(f"%{keyword}%")) |
                (cls.model.code.ilike(f"%{keyword}%"))
            )
        
        if app_type:
            filters.append(cls.model.app_type == app_type)
        
        if status:
            filters.append(cls.model.status == status)
        
        if owner_id:
            filters.append(cls.model.owner_id == owner_id)
        
        return await cls.get_list(db, page, page_size, filters)

    @classmethod
    async def publish(
        cls,
        db: AsyncSession,
        record_id: str,
        auto_commit: bool = True
    ) -> Optional[Application]:
        """
        发布应用（草稿 -> 已发布；已停用 -> 重新启用为已发布）

        :param db: 数据库会话
        :param record_id: 应用ID
        :param auto_commit: 是否自动提交
        :return: 更新后的应用或None
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            return None
        
        db_obj.status = "published"
        db_obj.version += 1
        
        if auto_commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
            await db.refresh(db_obj)
        
        return db_obj

    @classmethod
    async def disable(
        cls,
        db: AsyncSession,
        record_id: str,
        auto_commit: bool = True
    ) -> Optional[Application]:
        """
        停用应用
        
        :param db: 数据库会话
        :param record_id: 应用ID
        :param auto_commit: 是否自动提交
        :return: 更新后的应用或None
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            return None
        
        db_obj.status = "disabled"
        
        if auto_commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
            await db.refresh(db_obj)
        
        return db_obj

    @classmethod
    async def get_stats(
        cls,
        db: AsyncSession
    ) -> dict:
        """
        获取应用统计信息
        
        :param db: 数据库会话
        :return: 统计信息
        """
        # 总数
        total_result = await db.execute(
            select(func.count()).select_from(cls.model).where(
                cls.model.is_deleted == False  # noqa: E712
            )
        )
        total = total_result.scalar() or 0
        
        # 按状态统计
        status_result = await db.execute(
            select(cls.model.status, func.count()).where(
                cls.model.is_deleted == False  # noqa: E712
            ).group_by(cls.model.status)
        )
        status_stats = {row[0]: row[1] for row in status_result.all()}
        
        # 按类型统计
        type_result = await db.execute(
            select(cls.model.app_type, func.count()).where(
                cls.model.is_deleted == False  # noqa: E712
            ).group_by(cls.model.app_type)
        )
        type_stats = {row[0]: row[1] for row in type_result.all()}
        
        return {
            "total": total,
            "by_status": status_stats,
            "by_type": type_stats
        }
