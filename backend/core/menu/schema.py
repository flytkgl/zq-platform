#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Menu Schema - 菜单数据验证模式
字段名使用驼峰命名，与前端保持一致
"""
from datetime import datetime
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.base_schema import CSTDatetime


class MenuBase(BaseModel):
    """菜单基础Schema"""
    # 应用关联
    application_id: Optional[str] = Field(None, description="所属应用ID")
    is_system: bool = Field(default=False, description="是否为系统菜单")
    
    name: str = Field(..., description="菜单名称（路由名称）")
    title: Optional[str] = Field(None, description="菜单标题（显示名称）")
    authCode: Optional[str] = Field(None, description="后端权限标识")
    path: str = Field(..., description="路由路径")
    type: str = Field(default="catalog", description="菜单类型")
    
    # 路由配置
    component: Optional[str] = Field(None, description="组件路径")
    redirect: Optional[str] = Field(None, description="重定向路径")
    activePath: Optional[str] = Field(None, description="激活路径")
    query: Optional[Dict[str, Any]] = Field(None, description="额外路由参数")
    noBasicLayout: bool = Field(default=False, description="无需基础布局")
    
    # 菜单展示
    icon: Optional[str] = Field(None, description="菜单图标")
    activeIcon: Optional[str] = Field(None, description="激活图标")
    order: int = Field(default=0, description="菜单排序")
    hideInMenu: bool = Field(default=False, description="在菜单中隐藏")
    hideChildrenInMenu: bool = Field(default=False, description="在菜单中隐藏下级")
    hideInBreadcrumb: bool = Field(default=False, description="在面包屑中隐藏")
    
    # 标签页配置
    hideInTab: bool = Field(default=False, description="在标签栏中隐藏")
    affixTab: bool = Field(default=False, description="固定在标签栏")
    affixTabOrder: Optional[int] = Field(None, description="标签栏固定顺序")
    keepAlive: bool = Field(default=False, description="缓存页面")
    maxNumOfOpenTab: Optional[int] = Field(None, description="最大打开标签数")
    fullPathKey: bool = Field(default=True, description="路由完整路径作为key")
    
    # 外部链接配置
    link: Optional[str] = Field(None, description="外链URL")
    iframeSrc: Optional[str] = Field(None, description="内嵌iframe URL")
    openInNewWindow: bool = Field(default=False, description="在新窗口打开")
    
    # 徽标配置
    badge: Optional[str] = Field(None, description="徽标内容")
    badgeType: Optional[str] = Field(None, description="徽标类型")
    badgeVariants: Optional[str] = Field(None, description="徽标颜色")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证菜单名称格式"""
        if not v:
            raise ValueError('菜单名称不能为空')
        if not v[0].isalpha():
            raise ValueError('菜单名称必须以字母开头')
        if not all(c.isalnum() or c in '_-' for c in v):
            raise ValueError('菜单名称只能包含字母、数字、下划线和横线')
        return v
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """验证路由路径"""
        if not v:
            raise ValueError('路由路径不能为空')
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """验证菜单类型"""
        valid_types = ['catalog', 'menu', 'external', 'online_form', 'online_page', 'agent']
        if v not in valid_types:
            raise ValueError(f'菜单类型必须为 {", ".join(valid_types)} 之一')
        return v


class MenuCreate(MenuBase):
    """菜单创建Schema"""
    parent_id: Optional[str] = Field(None, description="父菜单ID")


class MenuUpdate(BaseModel):
    """菜单更新Schema - 所有字段可选"""
    # 应用关联
    application_id: Optional[str] = Field(None, description="所属应用ID")
    is_system: Optional[bool] = Field(None, description="是否为系统菜单")
    
    name: Optional[str] = Field(None, description="菜单名称")
    title: Optional[str] = Field(None, description="菜单标题")
    authCode: Optional[str] = Field(None, description="后端权限标识")
    path: Optional[str] = Field(None, description="路由路径")
    type: Optional[str] = Field(None, description="菜单类型")
    parent_id: Optional[str] = Field(None, description="父菜单ID")
    
    # 路由配置
    component: Optional[str] = Field(None, description="组件路径")
    redirect: Optional[str] = Field(None, description="重定向路径")
    activePath: Optional[str] = Field(None, description="激活路径")
    query: Optional[Dict[str, Any]] = Field(None, description="额外路由参数")
    noBasicLayout: Optional[bool] = Field(None, description="无需基础布局")
    
    # 菜单展示
    icon: Optional[str] = Field(None, description="菜单图标")
    activeIcon: Optional[str] = Field(None, description="激活图标")
    order: Optional[int] = Field(None, description="菜单排序")
    hideInMenu: Optional[bool] = Field(None, description="在菜单中隐藏")
    hideChildrenInMenu: Optional[bool] = Field(None, description="在菜单中隐藏下级")
    hideInBreadcrumb: Optional[bool] = Field(None, description="在面包屑中隐藏")
    
    # 标签页配置
    hideInTab: Optional[bool] = Field(None, description="在标签栏中隐藏")
    affixTab: Optional[bool] = Field(None, description="固定在标签栏")
    affixTabOrder: Optional[int] = Field(None, description="标签栏固定顺序")
    keepAlive: Optional[bool] = Field(None, description="缓存页面")
    maxNumOfOpenTab: Optional[int] = Field(None, description="最大打开标签数")
    fullPathKey: Optional[bool] = Field(None, description="路由完整路径作为key")
    
    # 外部链接配置
    link: Optional[str] = Field(None, description="外链URL")
    iframeSrc: Optional[str] = Field(None, description="内嵌iframe URL")
    openInNewWindow: Optional[bool] = Field(None, description="在新窗口打开")
    
    # 徽标配置
    badge: Optional[str] = Field(None, description="徽标内容")
    badgeType: Optional[str] = Field(None, description="徽标类型")
    badgeVariants: Optional[str] = Field(None, description="徽标颜色")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证菜单名称格式"""
        if v is not None:
            if not v:
                raise ValueError('菜单名称不能为空')
            if not v[0].isalpha():
                raise ValueError('菜单名称必须以字母开头')
            if not all(c.isalnum() or c in '_-' for c in v):
                raise ValueError('菜单名称只能包含字母、数字、下划线和横线')
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """验证菜单类型"""
        if v is not None:
            valid_types = ['catalog', 'menu', 'external', 'online_form', 'online_page', 'agent']
            if v not in valid_types:
                raise ValueError(f'菜单类型必须为 {", ".join(valid_types)} 之一')
        return v


class MenuResponse(BaseModel):
    """菜单响应Schema"""
    id: str
    parent_id: Optional[str] = None
    application_id: Optional[str] = None
    is_system: bool = False
    name: str
    title: Optional[str] = None
    authCode: Optional[str] = None
    path: str
    type: str
    
    # 路由配置
    component: Optional[str] = None
    redirect: Optional[str] = None
    activePath: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    noBasicLayout: bool = False
    
    # 菜单展示
    icon: Optional[str] = None
    activeIcon: Optional[str] = None
    order: int = 0
    hideInMenu: bool = False
    hideChildrenInMenu: bool = False
    hideInBreadcrumb: bool = False
    
    # 标签页配置
    hideInTab: bool = False
    affixTab: bool = False
    affixTabOrder: Optional[int] = None
    keepAlive: bool = False
    maxNumOfOpenTab: Optional[int] = None
    fullPathKey: bool = True
    
    # 外部链接配置
    link: Optional[str] = None
    iframeSrc: Optional[str] = None
    openInNewWindow: bool = False
    
    # 徽标配置
    badge: Optional[str] = None
    badgeType: Optional[str] = None
    badgeVariants: Optional[str] = None
    
    # 公共字段
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    # 计算字段
    level: Optional[int] = None
    childCount: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class MenuTreeNode(BaseModel):
    """菜单树节点"""
    id: str
    parent_id: Optional[str] = None
    name: str
    title: Optional[str] = None
    path: str
    type: str
    icon: Optional[str] = None
    order: int = 0
    level: int = 0
    childCount: int = 0
    children: List['MenuTreeNode'] = []
    
    model_config = ConfigDict(from_attributes=True)


class MenuSimple(BaseModel):
    """菜单简单输出（用于选择器）"""
    id: str
    name: str
    title: Optional[str] = None
    path: str
    type: str
    parent_id: Optional[str] = None
    level: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class MenuRouteNode(BaseModel):
    """菜单路由输出（前端路由格式）"""
    name: str
    path: str
    component: Optional[str] = None
    redirect: Optional[str] = None
    meta: Dict[str, Any] = {}
    children: List['MenuRouteNode'] = []
    
    model_config = ConfigDict(from_attributes=True)


class MenuBatchDeleteRequest(BaseModel):
    """批量删除菜单请求"""
    ids: List[str] = Field(..., description="要删除的菜单ID列表")


class MenuBatchDeleteResponse(BaseModel):
    """批量删除菜单响应"""
    count: int = Field(..., description="删除的记录数")
    failedIds: List[str] = Field(default=[], description="删除失败的ID列表")


class MenuPathResponse(BaseModel):
    """菜单路径响应"""
    menuId: str
    menuName: str
    path: List[MenuSimple] = Field(..., description="从根到当前菜单的路径")


class MenuStatsResponse(BaseModel):
    """菜单统计响应"""
    totalCount: int
    typeStats: Dict[str, int]
    maxLevel: int


class MenuMoveRequest(BaseModel):
    """移动菜单请求"""
    menuId: str = Field(..., description="要移动的菜单ID")
    newParentId: Optional[str] = Field(None, description="新父菜单ID，为空表示移动到根节点")


class MenuCheckNameRequest(BaseModel):
    """检查菜单名称请求"""
    name: str = Field(..., description="菜单名称")
    exclude_id: Optional[str] = Field(None, description="排除的菜单ID")


class MenuCheckPathRequest(BaseModel):
    """检查路由路径请求"""
    path: str = Field(..., description="路由路径")
    exclude_id: Optional[str] = Field(None, description="排除的菜单ID")
