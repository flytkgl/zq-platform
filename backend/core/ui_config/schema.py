#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI Config Schema - UI配置数据验证模式
"""
from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.base_schema import CSTDatetime


class UIConfigBase(BaseModel):
    """UI配置基础Schema"""
    application_id: Optional[str] = Field(default=None, description="所属应用ID（空为主应用配置）")
    config_key: str = Field(..., min_length=1, max_length=100, description="配置键")
    config_value: Optional[str] = Field(None, description="配置值(JSON)")
    config_type: str = Field(default="preferences", max_length=50, description="配置类型")
    description: Optional[str] = Field(None, max_length=200, description="配置描述")
    status: bool = Field(default=True, description="状态")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("config_key")
    @classmethod
    def validate_config_key(cls, v):
        """验证配置键格式"""
        if not v:
            raise ValueError("配置键不能为空")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("配置键只能包含字母、数字、下划线和短横线")
        return v


class UIConfigCreate(UIConfigBase):
    """UI配置创建Schema"""
    pass


class UIConfigUpdate(BaseModel):
    """UI配置更新Schema - 所有字段可选"""
    application_id: Optional[str] = Field(default=None, description="所属应用ID")
    config_key: Optional[str] = Field(None, min_length=1, max_length=100, description="配置键")
    config_value: Optional[str] = Field(None, description="配置值(JSON)")
    config_type: Optional[str] = Field(None, max_length=50, description="配置类型")
    description: Optional[str] = Field(None, max_length=200, description="配置描述")
    status: Optional[bool] = Field(None, description="状态")
    sort: Optional[int] = Field(None, description="排序")
    
    @field_validator("config_key")
    @classmethod
    def validate_config_key(cls, v):
        """验证配置键格式"""
        if v is not None:
            if not v:
                raise ValueError("配置键不能为空")
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError("配置键只能包含字母、数字、下划线和短横线")
        return v


class UIConfigResponse(BaseModel):
    """UI配置响应Schema"""
    id: str
    application_id: Optional[str] = None
    config_key: str
    config_value: Optional[str] = None
    config_type: str
    description: Optional[str] = None
    status: bool
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UIConfigSimple(BaseModel):
    """UI配置简单输出（用于选择器）"""
    id: str
    config_key: str
    config_type: str
    status: bool
    
    model_config = ConfigDict(from_attributes=True)


class UIConfigValueUpdate(BaseModel):
    """UI配置值更新Schema（仅更新值）"""
    config_value: str = Field(..., description="配置值(JSON)")


class PreferencesConfigResponse(BaseModel):
    """前端偏好配置响应Schema"""
    app: Optional[Dict[str, Any]] = None
    theme: Optional[Dict[str, Any]] = None
    logo: Optional[Dict[str, Any]] = None
    copyright: Optional[Dict[str, Any]] = None
    sidebar: Optional[Dict[str, Any]] = None
    header: Optional[Dict[str, Any]] = None
    footer: Optional[Dict[str, Any]] = None
    tabbar: Optional[Dict[str, Any]] = None
    breadcrumb: Optional[Dict[str, Any]] = None
    navigation: Optional[Dict[str, Any]] = None
    shortcutKeys: Optional[Dict[str, Any]] = None
    transition: Optional[Dict[str, Any]] = None
    widget: Optional[Dict[str, Any]] = None
    loginConfig: Optional[Dict[str, Any]] = None
