from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.base_schema import CSTDatetime


class DemoBase(BaseModel):
    """Demo基础Schema"""
    title: str
    content: Optional[str] = None
    status: int = 1
    priority: int = 0
    is_active: bool = True
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """验证状态"""
        if v not in [0, 1, 2]:
            raise ValueError("状态必须为 0(草稿)、1(发布) 或 2(归档)")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """验证优先级"""
        if v not in [0, 1, 2]:
            raise ValueError("优先级必须为 0(低)、1(中) 或 2(高)")
        return v


class DemoCreate(DemoBase):
    """创建Demo的Schema"""
    pass


class DemoUpdate(BaseModel):
    """更新Demo的Schema - 所有字段可选"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """验证状态"""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("状态必须为 0(草稿)、1(发布) 或 2(归档)")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """验证优先级"""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("优先级必须为 0(低)、1(中) 或 2(高)")
        return v


class DemoResponse(BaseModel):
    """
    Demo响应Schema - 演示字段权限
    
    必填字段（不可隐藏）：
    - id: 记录ID
    - title: 标题
    - status: 状态
    
    可选字段（可隐藏）：
    - content: 内容
    - priority: 优先级
    - is_active: 是否激活
    - sort: 排序
    - is_deleted: 是否删除
    - sys_create_datetime: 创建时间
    - sys_update_datetime: 更新时间
    - sys_creator_id: 创建人ID
    - sys_dept_id: 部门ID
    """
    # 必填字段 - 前端不可隐藏
    id: str
    status: int
    
    # 可选字段 - 前端可以隐藏
    title: Optional[str] = None
    content: Optional[str] = None
    priority: int = 0
    is_active: bool = True
    sort: Optional[int] = 0
    is_deleted: Optional[bool] = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    sys_creator_id: Optional[str] = None
    sys_dept_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
