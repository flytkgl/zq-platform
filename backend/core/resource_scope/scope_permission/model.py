#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ResourceDataScopeConfig Model - 资源数据权限配置模型
用于管理角色对不同资源类型的数据访问权限
"""
from sqlalchemy import Column, String, Integer, JSON, UniqueConstraint

from app.base_model import BaseModel


class ResourceDataScopeConfig(BaseModel):
    """
    资源数据权限配置模型
    
    用于配置角色对特定资源类型的数据访问范围
    
    字段说明：
    - role_id: 角色ID（逻辑外键关联core_role）
    - resource_type: 资源类型（如 'customer', 'order', 'post' 等）
    - data_scope: 数据权限范围（0-全部, 1-仅本人, 2-本部门, 3-本部门及下级, 4-自定义）
    - dept_ids: 自定义权限时的部门ID列表（JSON格式）
    
    示例：
    - role_id='role001', resource_type='customer', data_scope=4, dept_ids=['dept1', 'dept2']
      表示：角色role001对客户资源使用自定义权限，可以访问dept1和dept2的客户数据
    """
    __tablename__ = "core_resource_data_scope_config"
    
    # 数据权限范围选择
    DATA_SCOPE_CHOICES = {
        0: '全部数据',
        1: '仅本人数据',
        2: '本部门数据',
        3: '本部门及下级部门数据',
        4: '自定义数据',
    }
    
    # 角色ID（逻辑外键）
    role_id = Column(String(21), nullable=False, index=True, comment="角色ID（逻辑外键关联core_role）")
    
    # 资源类型
    resource_type = Column(String(50), nullable=False, index=True, comment="资源类型（如customer/order/post等）")
    
    # 数据权限范围
    data_scope = Column(Integer, default=0, comment="数据权限范围（0-全部, 1-仅本人, 2-本部门, 3-本部门及下级, 4-自定义）")
    
    # 自定义权限的部门ID列表
    dept_ids = Column(JSON, nullable=True, comment="自定义权限时的部门ID列表（JSON数组）")
    
    # 联合唯一约束：同一个角色对同一个资源类型只能有一条配置
    __table_args__ = (
        UniqueConstraint('role_id', 'resource_type', name='uq_role_resource'),
    )
    
    def __str__(self):
        return f"Role({self.role_id}) - Resource({self.resource_type}) - Scope({self.data_scope})"
    
    def get_data_scope_display(self) -> str:
        """获取数据权限范围的显示名称"""
        return self.DATA_SCOPE_CHOICES.get(self.data_scope, '未知')
