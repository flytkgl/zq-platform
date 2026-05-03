#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DictItem Model - 字典项模型
用于管理字典中的各个选项
"""
from sqlalchemy import Column, String, Boolean, Text

from app.base_model import BaseModel


class DictItem(BaseModel):
    """
    系统字典项表
    
    字段说明：
    - dict_id: 字典ID（逻辑外键）
    - label: 显示名称
    - value: 实际值
    - icon: 图标
    - status: 状态
    - remark: 备注
    """
    __tablename__ = "core_dict_item"
    
    # 字典ID（逻辑外键）
    dict_id = Column(String(36), nullable=False, index=True, comment="字典ID")
    
    # 显示名称
    label = Column(String(100), nullable=True, index=True, comment="显示名称")
    
    # 实际值
    value = Column(String(100), nullable=True, index=True, comment="实际值")
    
    # 图标
    icon = Column(String(100), nullable=True, comment="图标")
    
    # 状态
    status = Column(Boolean, default=True, index=True, comment="状态")
    
    # 备注
    remark = Column(Text, nullable=True, comment="备注")
    
    def __str__(self):
        return f"{self.label} ({self.value})"
