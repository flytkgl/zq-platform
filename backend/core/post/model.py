#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post Model - 岗位模型
用于管理组织中的岗位信息
"""
from sqlalchemy import Column, String, Integer, Boolean, Text

from app.base_model import BaseModel


class Post(BaseModel):
    """
    岗位模型 - 用于职位管理
    
    字段说明：
    - name: 岗位名称
    - code: 岗位编码（唯一）
    - post_type: 岗位类型（0-管理岗, 1-技术岗, 2-业务岗, 3-职能岗, 4-其他）
    - post_level: 岗位级别（0-高层, 1-中层, 2-基层, 3-一般员工）
    - status: 岗位状态（启用/禁用）
    - description: 岗位描述
    - dept_id: 所属部门ID（逻辑外键）
    """
    __tablename__ = "core_post"
    
    # 岗位类型选择
    POST_TYPE_CHOICES = {
        0: '管理岗',
        1: '技术岗',
        2: '业务岗',
        3: '职能岗',
        4: '其他',
    }
    
    # 岗位级别选择
    POST_LEVEL_CHOICES = {
        0: '高层',
        1: '中层',
        2: '基层',
        3: '一般员工',
    }
    
    # 岗位名称
    name = Column(String(64), nullable=False, index=True, comment="岗位名称")
    
    # 岗位编码
    code = Column(String(32), unique=True, nullable=False, index=True, comment="岗位编码")
    
    # 岗位类型
    post_type = Column(Integer, default=4, index=True, comment="岗位类型（0-管理岗, 1-技术岗, 2-业务岗, 3-职能岗, 4-其他）")
    
    # 岗位级别
    post_level = Column(Integer, default=3, index=True, comment="岗位级别（0-高层, 1-中层, 2-基层, 3-一般员工）")
    
    # 岗位状态
    status = Column(Boolean, default=True, index=True, comment="岗位状态（启用/禁用）")
    
    # 岗位描述
    description = Column(Text, nullable=True, comment="岗位描述/职责")
    
    # 所属部门（逻辑外键）
    dept_id = Column(String(21), nullable=True, index=True, comment="所属部门ID（逻辑外键关联core_dept）")
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_post_type_display(self) -> str:
        """获取岗位类型的显示名称"""
        return self.POST_TYPE_CHOICES.get(self.post_type, '未知')
    
    def get_post_level_display(self) -> str:
        """获取岗位级别的显示名称"""
        return self.POST_LEVEL_CHOICES.get(self.post_level, '未知')
