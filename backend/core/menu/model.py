#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Menu Model - 菜单模型
用于管理系统菜单和前端路由
"""
from sqlalchemy import Column, String, Boolean, Integer, JSON
from sqlalchemy.orm import relationship

from app.base_model import BaseModel


class Menu(BaseModel):
    """系统菜单表"""
    __tablename__ = "core_menu"

    # 所属应用（逻辑外键关联 core_application）
    application_id = Column(String(21), nullable=True, index=True, comment="所属应用ID")
    
    # 系统菜单标识（系统菜单在所有应用中都可见）
    is_system = Column(Boolean, default=False, comment="是否为系统菜单")

    # 基础信息（字段名使用驼峰，与前端保持一致）
    parent_id = Column("parent_id", String(21), nullable=True, index=True, comment="父菜单ID")
    name = Column(String(100), nullable=False, comment="菜单名称（路由名称）")
    title = Column(String(100), nullable=True, comment="菜单标题（显示名称）")
    authCode = Column(String(100), nullable=True, comment="后端权限标识")
    path = Column(String(200), nullable=False, comment="路由路径")
    type = Column(String(20), default="catalog", comment="菜单类型: catalog/menu/external/online_form/online_page/agent")

    # 路由配置
    component = Column(String(100), nullable=True, comment="组件路径")
    redirect = Column(String(200), nullable=True, comment="重定向路径")
    activePath = Column(String(200), nullable=True, comment="激活路径")
    query = Column(JSON, nullable=True, comment="额外路由参数")
    noBasicLayout = Column(Boolean, default=False, comment="无需基础布局")

    # 菜单展示
    icon = Column(String(100), nullable=True, comment="菜单图标")
    activeIcon = Column(String(100), nullable=True, comment="激活图标")
    order = Column(Integer, default=0, comment="菜单排序")
    hideInMenu = Column(Boolean, default=False, comment="在菜单中隐藏")
    hideChildrenInMenu = Column(Boolean, default=False, comment="在菜单中隐藏下级")
    hideInBreadcrumb = Column(Boolean, default=False, comment="在面包屑中隐藏")

    # 标签页配置
    hideInTab = Column(Boolean, default=False, comment="在标签栏中隐藏")
    affixTab = Column(Boolean, default=False, comment="固定在标签栏")
    affixTabOrder = Column(Integer, nullable=True, comment="标签栏固定顺序")
    keepAlive = Column(Boolean, default=False, comment="缓存页面")
    maxNumOfOpenTab = Column(Integer, nullable=True, comment="最大打开标签数")
    fullPathKey = Column(Boolean, default=True, comment="路由完整路径作为key（设为false时路径参数变化不刷新组件）")

    # 外部链接配置
    link = Column(String(500), nullable=True, comment="外链URL")
    iframeSrc = Column(String(500), nullable=True, comment="内嵌iframe URL")
    openInNewWindow = Column(Boolean, default=False, comment="在新窗口打开")

    # 徽标配置
    badge = Column(String(20), nullable=True, comment="徽标内容")
    badgeType = Column(String(20), nullable=True, comment="徽标类型: dot/normal")
    badgeVariants = Column(String(20), nullable=True, comment="徽标颜色")

    # 关系定义（使用primaryjoin指定逻辑关联，lazy='selectin'支持异步加载）
    parent = relationship(
        "Menu",
        remote_side="Menu.id",
        backref="children",
        foreign_keys="Menu.parent_id",
        primaryjoin="Menu.parent_id == Menu.id",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Menu {self.title or self.name} ({self.path})>"

    def get_type_display(self) -> str:
        """获取菜单类型显示名称"""
        type_map = {
            "catalog": "目录",
            "menu": "菜单",
            "external": "外部链接",
            "online_form": "在线表单",
            "online_page": "在线页面",
            "agent": "智能体",
        }
        return type_map.get(self.type, self.type)
