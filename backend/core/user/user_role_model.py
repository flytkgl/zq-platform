#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UserRole Model - 用户角色关联表
用于实现用户和角色的多对多关系
"""
from sqlalchemy import Column, String, Index

from app.base_model import BaseModel


class UserRole(BaseModel):
    """
    用户角色关联表
    
    实现用户和角色的多对多关系
    一个用户可以拥有多个角色
    一个角色可以分配给多个用户
    """
    __tablename__ = "core_user_role"
    
    # 用户ID（逻辑外键）
    user_id = Column(String(21), nullable=False, index=True, comment="用户ID")
    
    # 角色ID（逻辑外键）
    role_id = Column(String(21), nullable=False, index=True, comment="角色ID")
    
    # 创建联合唯一索引，确保同一用户不会重复分配同一角色
    __table_args__ = (
        Index('idx_user_role_unique', 'user_id', 'role_id', unique=True),
    )
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
