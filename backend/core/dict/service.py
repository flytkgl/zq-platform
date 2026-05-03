#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dict Service - 字典服务层
"""
from io import BytesIO
from typing import Tuple, Dict as DictType, Any, Optional, List

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.dict.model import Dict
from core.dict.schema import DictCreate, DictUpdate


class DictService(BaseService[Dict, DictCreate, DictUpdate]):
    """
    字典服务层
    继承BaseService，自动获得增删改查功能
    
    数据权限：
    - 使用 get_list_with_data_scope() 自动应用数据权限
    - 支持本人、本部门、本部门及下级、全部等数据范围
    """
    
    model = Dict
    
    # 资源类型（用于数据权限配置）
    RESOURCE_TYPE = "dict"
    RESOURCE_DISPLAY_NAME = "字典管理"
    
    # Excel导入导出配置
    excel_columns = {
        "name": "字典名称",
        "code": "字典编码",
        "status": "状态",
        "remark": "备注",
    }
    excel_sheet_name = "字典列表"
    
    @classmethod
    def _export_converter(cls, item: Any) -> DictType[str, Any]:
        """导出数据转换器"""
        return {
            "name": item.name,
            "code": item.code,
            "status": "启用" if item.status else "禁用",
            "remark": item.remark or "",
        }
    
    @classmethod
    def _import_processor(cls, row: DictType[str, Any]) -> Optional[Dict]:
        """导入数据处理器"""
        name = row.get("name")
        code = row.get("code")
        if not name or not code:
            return None
        
        status_str = row.get("status", "启用")
        status = status_str in ("启用", "true", "True", "1", True)
        
        return Dict(
            name=str(name),
            code=str(code),
            status=status,
            remark=str(row.get("remark") or ""),
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
    async def get_by_code(cls, db: AsyncSession, code: str) -> Optional[Dict]:
        """根据编码获取字典"""
        result = await db.execute(
            select(Dict).where(
                Dict.code == code,
                Dict.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_all_active(cls, db: AsyncSession, application_id: str = None) -> List[Dict]:
        """获取所有启用的字典（包含全局可见的字典）"""
        conditions = [
            Dict.status == True,  # noqa: E712
            Dict.is_deleted == False  # noqa: E712
        ]
        if application_id:
            conditions.append(or_(
                Dict.application_id == application_id,
                Dict.is_global == True  # noqa: E712
            ))
        else:
            conditions.append(or_(
                Dict.application_id.is_(None),
                Dict.is_global == True  # noqa: E712
            ))
        
        result = await db.execute(
            select(Dict).where(*conditions).order_by(Dict.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """搜索字典"""
        filters = [
            or_(
                Dict.name.ilike(f"%{keyword}%"),
                Dict.code.ilike(f"%{keyword}%"),
            )
        ]
        return await cls.get_list(db, page=page, page_size=page_size, filters=filters)
    
    @classmethod
    async def batch_delete(
        cls,
        db: AsyncSession,
        ids: List[str],
        hard: bool = False
    ) -> Tuple[int, List[str]]:
        """
        批量删除字典
        
        :return: (成功数量, 失败的ID列表)
        """
        success_count = 0
        failed_ids = []
        
        for dict_id in ids:
            try:
                success = await cls.delete(db, record_id=dict_id, hard=hard)
                if success:
                    success_count += 1
                else:
                    failed_ids.append(dict_id)
            except Exception:
                failed_ids.append(dict_id)
        
        return success_count, failed_ids
    
    @classmethod
    async def batch_update_status(
        cls,
        db: AsyncSession,
        ids: List[str],
        status: bool
    ) -> int:
        """批量更新字典状态"""
        count = 0
        for dict_id in ids:
            dict_obj = await cls.get_by_id(db, dict_id)
            if dict_obj:
                dict_obj.status = status
                await db.commit()
                count += 1
        return count
