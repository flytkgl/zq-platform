#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Role Model - 角色模型
用于管理系统角色和权限分配
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.base_model import BaseModel
from app.database import Base


# 角色-菜单关联表
role_menu = Table(
    'core_role_menu',
    Base.metadata,
    Column('role_id', String(21), ForeignKey('core_role.id', ondelete='CASCADE'), primary_key=True),
    Column('menu_id', String(21), ForeignKey('core_menu.id', ondelete='CASCADE'), primary_key=True),
)

# 角色-权限关联表
role_permission = Table(
    'core_role_permission',
    Base.metadata,
    Column('role_id', String(21), ForeignKey('core_role.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', String(21), ForeignKey('core_permission.id', ondelete='CASCADE'), primary_key=True),
)

# 角色-部门关联表
role_dept = Table(
    'core_role_dept',
    Base.metadata,
    Column('role_id', String(21), ForeignKey('core_role.id', ondelete='CASCADE'), primary_key=True),
    Column('dept_id', String(21), ForeignKey('core_dept.id', ondelete='CASCADE'), primary_key=True),
)


class Role(BaseModel):
    """
    角色模型 - 用于用户角色管理和权限分配
    
    字段说明：
    - name: 角色名称
    - code: 角色编码（唯一）
    - role_type: 角色类型（0-系统角色, 1-自定义角色）
    - status: 角色状态
    - priority: 角色优先级
    - description: 角色描述
    - remark: 备注
    """
    __tablename__ = "core_role"
    
    # 角色类型选择
    ROLE_TYPE_CHOICES = {
        0: '系统角色',
        1: '自定义角色',
    }
    
    # 角色名称
    name = Column(String(64), nullable=False, index=True, comment="角色名称")
    
    # 角色编码
    code = Column(String(64), unique=True, nullable=False, index=True, comment="角色编码")
    
    # 角色类型
    role_type = Column(Integer, default=1, index=True, comment="角色类型（0-系统角色, 1-自定义角色）")
    
    # 角色状态
    status = Column(Boolean, default=True, index=True, comment="角色状态（启用/禁用）")
    
    # 角色优先级
    priority = Column(Integer, default=0, index=True, comment="角色优先级（数字越大优先级越高）")
    
    # 角色描述
    description = Column(Text, nullable=True, comment="角色描述")
    
    # 备注
    remark = Column(Text, nullable=True, comment="备注信息")
    
    # 多对多关系
    menus = relationship("Menu", secondary=role_menu, backref="roles", lazy="selectin")
    permissions = relationship("Permission", secondary=role_permission, backref="roles", lazy="selectin")
    depts = relationship("Dept", secondary=role_dept, backref="roles", lazy="selectin")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def is_system_role(self) -> bool:
        """判断是否为系统角色"""
        return self.role_type == 0
    
    def can_delete(self) -> bool:
        """判断是否可以删除（系统角色不可删除）"""
        return self.role_type != 0
    
    def get_role_type_display(self) -> str:
        """获取角色类型的显示名称"""
        return self.ROLE_TYPE_CHOICES.get(self.role_type, '未知')
