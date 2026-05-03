#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dept Model - 部门模型
用于管理组织架构中的部门信息
"""
from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship

from app.base_model import BaseModel


class Dept(BaseModel):
    """
    部门模型 - 用于组织架构管理
    
    字段说明：
    - name: 部门名称
    - code: 部门编码（唯一）
    - dept_type: 部门类型（company/department/team/other）
    - phone: 部门电话
    - email: 部门邮箱
    - status: 部门状态（启用/禁用）
    - description: 部门描述
    - parent_id: 父部门ID
    - lead_id: 部门领导ID
    - level: 部门层级（0为顶层）
    - path: 部门路径（便于查询，格式：/id1/id2/）
    """
    __tablename__ = "core_dept"

    # 部门名称
    name = Column(String(64), nullable=False, index=True, comment="部门名称")
    
    # 部门编码
    code = Column(String(32), unique=True, nullable=True, index=True, comment="部门编码")
    
    # 部门类型：company-公司, department-部门, team-小组, other-其他
    dept_type = Column(String(20), default="department", index=True, comment="部门类型")
    
    # 部门电话
    phone = Column(String(20), nullable=True, comment="部门电话")
    
    # 部门邮箱
    email = Column(String(64), nullable=True, comment="部门邮箱")
    
    # 部门状态
    status = Column(Boolean, default=True, index=True, comment="部门状态")
    
    # 部门描述
    description = Column(Text, nullable=True, comment="部门描述")
    
    # 父部门ID（逻辑外键，不创建数据库约束）
    parent_id = Column(String(21), nullable=True, index=True, comment="父部门ID")
    
    # 部门领导ID（逻辑外键，不创建数据库约束）
    lead_id = Column(String(21), nullable=True, comment="部门领导ID")
    
    # 部门层级（0为顶层）
    level = Column(Integer, default=0, index=True, comment="部门层级")
    
    # 部门路径（便于查询，格式：/id1/id2/）
    path = Column(String(500), nullable=True, index=True, comment="部门路径")
    
    # 钉钉部门ID（用于组织架构同步映射）
    dingtalk_dept_id = Column(String(64), unique=True, nullable=True, index=True, comment="钉钉部门ID")

    # 企业微信部门ID（用于组织架构同步映射）
    wecom_dept_id = Column(String(64), unique=True, nullable=True, index=True, comment="企业微信部门ID")

    # 飞书部门ID（用于组织架构同步映射，open_department_id 格式）
    feishu_dept_id = Column(String(128), unique=True, nullable=True, index=True, comment="飞书部门ID")
    
    # 关系定义（使用primaryjoin指定逻辑关联，lazy='selectin'支持异步加载）
    parent = relationship("Dept", remote_side="Dept.id", backref="children", foreign_keys="Dept.parent_id", primaryjoin="Dept.parent_id == Dept.id", lazy="selectin")
    lead = relationship("User", foreign_keys="Dept.lead_id", primaryjoin="Dept.lead_id == User.id", backref="leading_depts", lazy="selectin")
    
    def __repr__(self):
        return f"<Dept {self.name} ({self.code or 'N/A'})>"
    
    def get_dept_type_display(self) -> str:
        """获取部门类型的显示名称"""
        type_map = {
            "company": "公司",
            "department": "部门",
            "team": "小组",
            "other": "其他",
        }
        return type_map.get(self.dept_type, "未知")
    
    def get_full_name(self) -> str:
        """获取部门全名（包含父部门）"""
        if self.parent:
            return f"{self.parent.get_full_name()} / {self.name}"
        return self.name
