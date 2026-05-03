#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User Schema - 用户数据验证模式
"""
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr

from app.base_schema import CSTDatetime


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=150, description="用户名")
    email: Optional[str] = Field(None, max_length=255, description="邮箱")
    mobile: Optional[str] = Field(None, max_length=11, description="手机号")
    avatar: Optional[str] = Field(None, max_length=36, description="头像UUID")
    name: Optional[str] = Field(None, max_length=64, description="真实姓名")
    gender: int = Field(default=0, ge=0, le=2, description="性别：0-未知, 1-男, 2-女")
    user_type: int = Field(default=1, ge=0, le=2, description="用户类型：0-系统用户, 1-普通用户, 2-外部用户")
    user_status: int = Field(default=1, ge=0, le=2, description="用户状态：0-禁用, 1-正常, 2-锁定")
    birthday: Optional[date] = Field(None, description="生日")
    city: Optional[str] = Field(None, max_length=100, description="所在城市")
    address: Optional[str] = Field(None, max_length=200, description="详细地址")
    bio: Optional[str] = Field(None, description="个人简介")
    is_active: bool = Field(default=True, description="是否激活")
    dept_id: Optional[str] = Field(None, description="所属部门ID")
    manager_id: Optional[str] = Field(None, description="直属上级ID")
    role_ids: Optional[List[str]] = Field(default=None, description="角色ID列表")
    sort: int = Field(default=0, description="排序")
    
    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        """验证手机号"""
        if v:
            if not v.isdigit():
                raise ValueError("手机号只能包含数字")
            if len(v) != 11:
                raise ValueError("手机号必须为11位")
        return v
    
    @field_validator("user_status")
    @classmethod
    def validate_user_status(cls, v):
        """验证用户状态"""
        if v not in [0, 1, 2]:
            raise ValueError("用户状态必须为 0(禁用)、1(正常) 或 2(锁定)")
        return v
    
    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v):
        """验证用户类型"""
        if v not in [0, 1, 2]:
            raise ValueError("用户类型必须为 0(系统用户)、1(普通用户) 或 2(外部用户)")
        return v
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        """验证性别"""
        if v not in [0, 1, 2]:
            raise ValueError("性别必须为 0(未知)、1(男) 或 2(女)")
        return v


class UserCreate(UserBase):
    """用户创建Schema"""
    # password: str = Field(..., min_length=6, max_length=20, description="密码")
    pass


class UserUpdate(BaseModel):
    """用户更新Schema - 所有字段可选"""
    username: Optional[str] = Field(None, min_length=3, max_length=150, description="用户名")
    email: Optional[str] = Field(None, max_length=255, description="邮箱")
    mobile: Optional[str] = Field(None, max_length=11, description="手机号")
    avatar: Optional[str] = Field(None, max_length=36, description="头像UUID")
    name: Optional[str] = Field(None, max_length=64, description="真实姓名")
    gender: Optional[int] = Field(None, ge=0, le=2, description="性别")
    user_type: Optional[int] = Field(None, ge=0, le=2, description="用户类型")
    user_status: Optional[int] = Field(None, ge=0, le=2, description="用户状态")
    birthday: Optional[date] = Field(None, description="生日")
    city: Optional[str] = Field(None, max_length=100, description="所在城市")
    address: Optional[str] = Field(None, max_length=200, description="详细地址")
    bio: Optional[str] = Field(None, description="个人简介")
    is_active: Optional[bool] = Field(None, description="是否激活")
    dept_id: Optional[str] = Field(None, description="所属部门ID")
    manager_id: Optional[str] = Field(None, description="直属上级ID")
    role_ids: Optional[List[str]] = Field(None, description="角色ID列表")
    sort: Optional[int] = Field(None, description="排序")
    
    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        """验证手机号"""
        if v is not None and v:
            if not v.isdigit():
                raise ValueError("手机号只能包含数字")
            if len(v) != 11:
                raise ValueError("手机号必须为11位")
        return v
    
    @field_validator("user_status")
    @classmethod
    def validate_user_status(cls, v):
        """验证用户状态"""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("用户状态必须为 0(禁用)、1(正常) 或 2(锁定)")
        return v
    
    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v):
        """验证用户类型"""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("用户类型必须为 0(系统用户)、1(普通用户) 或 2(外部用户)")
        return v
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        """验证性别"""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("性别必须为 0(未知)、1(男) 或 2(女)")
        return v


class UserResponse(BaseModel):
    """用户响应Schema"""
    id: str
    username: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    avatar: Optional[str] = None
    name: Optional[str] = None
    gender: int = 0
    gender_display: Optional[str] = None
    user_type: int = 1
    user_type_display: Optional[str] = None
    user_status: int = 1
    user_status_display: Optional[str] = None
    birthday: Optional[date] = None
    city: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None
    is_superuser: bool = False
    is_active: bool = True
    dept_id: Optional[str] = None
    post_id: Optional[str] = None
    post_name: Optional[str] = None
    manager_id: Optional[str] = None
    role_ids: Optional[List[str]] = None
    last_login: Optional[CSTDatetime] = None
    last_login_ip: Optional[str] = None
    last_login_type: Optional[str] = None
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserSimple(BaseModel):
    """用户简单输出（用于选择器）"""
    id: str
    name: Optional[str] = None
    username: str
    avatar: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    dept_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrgChartNode(BaseModel):
    """组织架构节点"""
    id: str
    name: Optional[str] = None
    username: str
    avatar: Optional[str] = None
    dept_name: Optional[str] = None
    post_name: Optional[str] = None
    subordinate_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class OrgChartChainNode(BaseModel):
    """组织架构汇报链节点（嵌套结构）"""
    id: str
    name: Optional[str] = None
    username: str
    avatar: Optional[str] = None
    dept_name: Optional[str] = None
    post_name: Optional[str] = None
    subordinate_count: int = 0
    children: List["OrgChartChainNode"] = []

    model_config = ConfigDict(from_attributes=True)


class UserPasswordResetIn(BaseModel):
    """重置密码输入"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v, info):
        """验证确认密码"""
        if info.data.get("new_password") and v != info.data.get("new_password"):
            raise ValueError("两次输入的密码不一致")
        return v


class UserPasswordSetIn(BaseModel):
    """管理员设置密码输入"""
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


class UserBatchDeleteIn(BaseModel):
    """批量删除用户输入"""
    ids: List[str] = Field(..., description="要删除的用户ID列表")


class UserBatchDeleteOut(BaseModel):
    """批量删除用户输出"""
    success_count: int = Field(..., description="删除的记录数")
    fail_count: int = Field(..., description="删除失败的ID列表")


class UserBatchUpdateStatusIn(BaseModel):
    """批量更新用户状态输入"""
    ids: List[str] = Field(..., description="用户ID列表")
    user_status: int = Field(..., ge=0, le=2, description="用户状态：0-禁用，1-正常，2-锁定")
    
    @field_validator("user_status")
    @classmethod
    def validate_user_status(cls, v):
        """验证用户状态"""
        if v not in [0, 1, 2]:
            raise ValueError("用户状态必须为 0(禁用)、1(正常) 或 2(锁定)")
        return v


class UserBatchUpdateStatusOut(BaseModel):
    """批量更新用户状态输出"""
    count: int = Field(..., description="更新的记录数")


class UserProfileUpdateIn(BaseModel):
    """用户个人信息更新输入"""
    name: Optional[str] = Field(None, max_length=64, description="真实姓名")
    email: Optional[str] = Field(None, max_length=255, description="邮箱")
    mobile: Optional[str] = Field(None, max_length=11, description="手机号")
    avatar: Optional[str] = Field(None, max_length=36, description="头像UUID")
    gender: Optional[int] = Field(None, ge=0, le=2, description="性别")
    birthday: Optional[date] = Field(None, description="生日")
    city: Optional[str] = Field(None, max_length=100, description="所在城市")
    address: Optional[str] = Field(None, max_length=200, description="详细地址")
    bio: Optional[str] = Field(None, description="个人简介")
    
    @field_validator("birthday", mode="before")
    @classmethod
    def validate_birthday(cls, v):
        """验证生日，将空字符串转换为None"""
        if v == "" or v is None:
            return None
        return v
    
    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        """验证手机号"""
        if v is not None and v:
            if not v.isdigit():
                raise ValueError("手机号只能包含数字")
            if len(v) != 11:
                raise ValueError("手机号必须为11位")
        return v
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        """验证性别"""
        if v is not None and v not in [0, 1, 2]:
            raise ValueError("性别必须为 0(未知)、1(男) 或 2(女)")
        return v
