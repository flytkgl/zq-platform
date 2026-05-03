#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Permission Model - 权限模型
用于管理系统中的操作权限（如按钮权限、接口权限等）
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, UniqueConstraint

from app.base_model import BaseModel


class Permission(BaseModel):
    """
    权限模型 - 用于细粒度的权限控制
    
    字段说明：
    - menu_id: 关联的菜单ID（逻辑外键）
    - name: 权限名称
    - code: 权限编码
    - permission_type: 权限类型（0-按钮权限, 1-API权限, 3-其他权限）
    - api_path: API路径
    - http_method: HTTP方法（0-GET, 1-POST, 2-PUT, 3-DELETE, 4-PATCH, 5-ALL）
    - description: 权限描述
    - is_active: 是否启用
    
    注意：数据权限已迁移到 ResourceDataScopeConfig 模型，按资源类型进行配置
    """
    __tablename__ = "core_permission"
    
    # 权限类型选择
    PERMISSION_TYPE_CHOICES = {
        0: '按钮权限',
        1: 'API权限',
        3: '其他权限',
    }
    
    # HTTP方法选择
    HTTP_METHOD_CHOICES = {
        0: 'GET',
        1: 'POST',
        2: 'PUT',
        3: 'DELETE',
        4: 'PATCH',
        5: 'ALL',
    }
    
    # 关联的菜单ID（逻辑外键）
    menu_id = Column(String(21), nullable=False, index=True, comment="关联菜单ID（逻辑外键关联core_menu）")
    
    # 权限名称
    name = Column(String(64), nullable=False, index=True, comment="权限名称")
    
    # 权限编码
    code = Column(String(64), nullable=False, index=True, comment="权限编码")
    
    # 权限类型
    permission_type = Column(Integer, default=0, index=True, comment="权限类型（1-API权限")
    
    # API路径
    api_path = Column(String(200), nullable=True, comment="API路径")
    
    # HTTP方法
    http_method = Column(Integer, default=0, comment="HTTP方法（0-GET, 1-POST, 2-PUT, 3-DELETE, 4-PATCH, 5-ALL）")
    
    # 权限描述
    description = Column(Text, nullable=True, comment="权限描述")
    
    # 是否启用
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    
    # 联合唯一约束：同一个菜单下的权限编码必须唯一
    __table_args__ = (
        UniqueConstraint('menu_id', 'code', name='uq_permission_menu_code'),
    )
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_http_method_display(self) -> str:
        """获取HTTP方法的显示名称"""
        return self.HTTP_METHOD_CHOICES.get(self.http_method, 'UNKNOWN')
    
    def get_permission_type_display(self) -> str:
        """获取权限类型的显示名称"""
        return self.PERMISSION_TYPE_CHOICES.get(self.permission_type, '未知')
