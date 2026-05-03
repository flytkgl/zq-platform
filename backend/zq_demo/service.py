from io import BytesIO
from typing import Tuple, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from app.field_metadata_generator import generate_field_metadata_from_schema
from zq_demo.model import Demo
from zq_demo.schema import DemoCreate, DemoUpdate, DemoResponse


class DemoService(BaseService[Demo, DemoCreate, DemoUpdate]):
    """
    Demo服务层 - 演示数据权限和字段权限
    
    功能：
    1. 数据权限（行权限）：根据用户角色过滤数据
       - 使用 get_list_with_data_scope() 自动应用数据权限
       - 支持本人、本部门、本部门及下级、全部等数据范围
    
    2. 字段权限（列权限）：根据角色配置隐藏/脱敏字段
       - 使用 apply_field_permissions_auto() 自动应用字段权限
       - 必填字段（id、title、status）不可隐藏
       - 可选字段（content、priority等）可以隐藏
    
    3. Excel导入导出：支持带数据权限的导出
       - 使用 export_to_excel_with_data_scope() 导出
    """
    
    model = Demo
    
    # 资源显示名称（用于前端显示）
    RESOURCE_DISPLAY_NAME = "Demo示例"
    
    # 从 Response Schema 生成字段元数据
    # 必填字段会被标记为 required=True，前端禁止隐藏
    FIELD_METADATA = generate_field_metadata_from_schema(DemoResponse, Demo)
    
    # Excel导入导出配置
    excel_columns = {
        "title": "标题",
        "content": "内容",
        "status": "状态",
        "priority": "优先级",
        "is_active": "是否激活",
    }
    excel_sheet_name = "Demo列表"
    
    @classmethod
    def _export_converter(cls, item: Any) -> Dict[str, Any]:
        """导出数据转换器"""
        status_map = {0: "草稿", 1: "发布", 2: "归档"}
        priority_map = {0: "低", 1: "中", 2: "高"}
        
        return {
            "title": item.title,
            "content": item.content or "",
            "status": status_map.get(item.status, "未知"),
            "priority": priority_map.get(item.priority, "未知"),
            "is_active": "是" if item.is_active else "否",
        }
    
    @classmethod
    def _import_processor(cls, row: Dict[str, Any]) -> Optional[Demo]:
        """导入数据处理器"""
        title = row.get("title")
        if not title:
            return None
        
        # 状态转换
        status_str = row.get("status", "发布")
        status_map = {"草稿": 0, "发布": 1, "归档": 2}
        status = status_map.get(status_str, 1)
        
        # 优先级转换
        priority_str = row.get("priority", "低")
        priority_map = {"低": 0, "中": 1, "高": 2}
        priority = priority_map.get(priority_str, 0)
        
        # 是否激活转换
        is_active_str = row.get("is_active", "是")
        is_active = is_active_str in ("是", "true", "True", "1", True)
        
        return Demo(
            title=str(title),
            content=str(row.get("content") or ""),
            status=status,
            priority=priority,
            is_active=is_active
        )
    
    @classmethod
    async def export_to_excel(
        cls,
        db: AsyncSession,
        data_converter: Any = None
    ) -> BytesIO:
        """导出所有Demo到Excel"""
        return await super().export_to_excel(db, cls._export_converter)
    
    @classmethod
    async def import_from_excel(
        cls,
        db: AsyncSession,
        file_content: bytes,
        row_processor: Any = None
    ) -> Tuple[int, int]:
        """从Excel导入Demo"""
        return await super().import_from_excel(db, file_content, cls._import_processor)
