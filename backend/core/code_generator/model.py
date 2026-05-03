#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编码生成器数据模型
"""
from sqlalchemy import Column, String, Integer, Index
from app.base_model import BaseModel


class CodeSequence(BaseModel):
    """编码序号表"""
    __tablename__ = "code_sequence"

    business_type = Column(String(100), nullable=False, comment="业务类型")
    prefix = Column(String(50), default="", comment="前缀")
    date_key = Column(String(20), default="", comment="日期键（用于按日期重置）")
    current_seq = Column(Integer, default=0, comment="当前序号")
    
    __table_args__ = (
        Index('idx_business_prefix_date', 'business_type', 'prefix', 'date_key'),
    )
