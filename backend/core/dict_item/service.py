#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DictItem Service - 字典项服务层
"""
from io import BytesIO
from typing import Tuple, Dict, Any, Optional, List

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.dict_item.model import DictItem
from core.dict_item.schema import DictItemCreate, DictItemUpdate


class DictItemService(BaseService[DictItem, DictItemCreate, DictItemUpdate]):
    """
    字典项服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = DictItem
    
    # Excel导入导出配置
    excel_columns = {
        "label": "显示名称",
        "value": "实际值",
        "icon": "图标",
        "status": "状态",
        "remark": "备注",
    }
    excel_sheet_name = "字典项列表"
    
    @classmethod
    def _export_converter(cls, item: Any) -> Dict[str, Any]:
        """导出数据转换器"""
        return {
            "label": item.label or "",
            "value": item.value or "",
            "icon": item.icon or "",
            "status": "启用" if item.status else "禁用",
            "remark": item.remark or "",
        }
    
    @classmethod
    def _import_processor(cls, row: Dict[str, Any]) -> Optional[DictItem]:
        """导入数据处理器"""
        label = row.get("label")
        value = row.get("value")
        if not label and not value:
            return None
        
        status_str = row.get("status", "启用")
        status = status_str in ("启用", "true", "True", "1", True)
        
        return DictItem(
            label=str(label) if label else None,
            value=str(value) if value else None,
            icon=str(row.get("icon") or "") if row.get("icon") else None,
            status=status,
            remark=str(row.get("remark") or "") if row.get("remark") else None,
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
    async def get_by_dict_id(cls, db: AsyncSession, dict_id: str) -> List[DictItem]:
        """根据字典ID获取字典项列表"""
        result = await db.execute(
            select(DictItem).where(
                DictItem.dict_id == dict_id,
                DictItem.is_deleted == False  # noqa: E712
            ).order_by(DictItem.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_dict_code(cls, db: AsyncSession, dict_code: str) -> List[DictItem]:
        """根据字典编码获取字典项列表"""
        from core.dict.model import Dict as DictModel
        
        # 先获取字典
        dict_result = await db.execute(
            select(DictModel).where(
                DictModel.code == dict_code,
                DictModel.is_deleted == False  # noqa: E712
            )
        )
        dict_obj = dict_result.scalar_one_or_none()
        
        if not dict_obj:
            return []
        
        # 获取字典项
        return await cls.get_by_dict_id(db, dict_obj.id)
    
    @classmethod
    async def get_all_active(cls, db: AsyncSession) -> List[DictItem]:
        """获取所有启用的字典项"""
        result = await db.execute(
            select(DictItem).where(
                DictItem.status == True,  # noqa: E712
                DictItem.is_deleted == False  # noqa: E712
            ).order_by(DictItem.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def search(
        cls,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DictItem], int]:
        """搜索字典项"""
        filters = [
            or_(
                DictItem.label.ilike(f"%{keyword}%"),
                DictItem.value.ilike(f"%{keyword}%"),
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
        批量删除字典项
        
        :return: (成功数量, 失败的ID列表)
        """
        success_count = 0
        failed_ids = []
        
        for item_id in ids:
            try:
                success = await cls.delete(db, record_id=item_id, hard=hard)
                if success:
                    success_count += 1
                else:
                    failed_ids.append(item_id)
            except Exception:
                failed_ids.append(item_id)
        
        return success_count, failed_ids
    
    @classmethod
    async def batch_update_status(
        cls,
        db: AsyncSession,
        ids: List[str],
        status: bool
    ) -> int:
        """批量更新字典项状态"""
        count = 0
        for item_id in ids:
            item = await cls.get_by_id(db, item_id)
            if item:
                item.status = status
                await db.commit()
                count += 1
        return count
