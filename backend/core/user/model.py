#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User Model - 用户模型
用于管理系统用户
"""
from datetime import date

from sqlalchemy import Column, String, Text, Boolean, Integer, Date, DateTime
from sqlalchemy.orm import relationship

from app.base_model import BaseModel


class User(BaseModel):
    """
    用户模型 - 系统用户管理
    
    字段说明：
    - username: 用户名（唯一）
    - password: 密码（加密存储）
    - is_superuser: 是否为超级管理员
    - email: 邮箱
    - mobile: 手机号
    - avatar: 头像
    - name: 真实姓名
    - gender: 性别（0-未知, 1-男, 2-女）
    - user_type: 用户类型（0-系统用户, 1-普通用户, 2-外部用户）
    - user_status: 用户状态（0-禁用, 1-正常, 2-锁定）
    - dept_id: 所属部门ID
    - manager_id: 直属上级ID
    - is_active: 是否激活
    """
    __tablename__ = "core_user"

    # 用户名
    username = Column(String(150), unique=True, nullable=False, index=True, comment="用户名")
    
    # 密码（加密存储，OAuth用户可为空）
    password = Column(String(128), nullable=True, comment="密码")
    
    # 是否为超级管理员
    is_superuser = Column(Boolean, default=False, index=True, comment="是否超级管理员")
    
    # 最后登录时间
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 邮箱
    email = Column(String(255), nullable=True, index=True, comment="邮箱")
    
    # 手机号
    mobile = Column(String(11), nullable=True, index=True, comment="手机号")
    
    # 头像
    avatar = Column(String(36), nullable=True, comment="头像UUID")
    
    # 真实姓名
    name = Column(String(64), nullable=True, index=True, comment="真实姓名")
    
    # 性别：0-未知, 1-男, 2-女
    gender = Column(Integer, default=0, nullable=True, comment="性别")
    
    # 用户类型：0-系统用户, 1-普通用户, 2-外部用户
    user_type = Column(Integer, default=1, index=True, comment="用户类型")
    
    # 用户状态：0-禁用, 1-正常, 2-锁定
    user_status = Column(Integer, default=1, index=True, comment="用户状态")
    
    # 生日
    birthday = Column(Date, nullable=True, comment="生日")
    
    # 所在城市
    city = Column(String(100), nullable=True, comment="所在城市")
    
    # 地址
    address = Column(String(200), nullable=True, comment="详细地址")
    
    # 个人简介
    bio = Column(Text, nullable=True, comment="个人简介")
    
    # 最后登录IP
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    
    # 最后登录方式
    last_login_type = Column(String(20), nullable=True, index=True, comment="最后登录方式")
    
    # 是否激活
    is_active = Column(Boolean, default=True, index=True, comment="是否激活")
    
    # 所属部门ID（逻辑外键，不创建数据库约束）
    dept_id = Column(String(21), nullable=True, index=True, comment="所属部门ID")
    
    # 所属岗位ID（逻辑外键，不创建数据库约束）
    post_id = Column(String(21), nullable=True, index=True, comment="所属岗位ID")
    
    # 所属角色ID（逻辑外键，不创建数据库约束）
    # 注意：已改为多对多关系，通过 core_user_role 表关联
    # 保留此字段用于数据迁移，后续版本可删除
    role_id = Column(String(21), nullable=True, index=True, comment="所属角色ID(已废弃)")
    
    # 直属上级ID（逻辑外键，不创建数据库约束）
    manager_id = Column(String(21), nullable=True, comment="直属上级ID")
    
    # OAuth 相关字段
    oauth_provider = Column(String(50), nullable=True, index=True, comment="OAuth提供商")
    gitee_id = Column(String(200), unique=True, nullable=True, index=True, comment="Gitee用户ID")
    github_id = Column(String(200), unique=True, nullable=True, index=True, comment="GitHub用户ID")
    qq_id = Column(String(200), unique=True, nullable=True, index=True, comment="QQ用户openid")
    google_id = Column(String(200), unique=True, nullable=True, index=True, comment="Google用户ID")
    wechat_unionid = Column(String(200), unique=True, nullable=True, index=True, comment="微信UnionID")
    wechat_openid = Column(String(200), nullable=True, index=True, comment="微信OpenID")
    microsoft_id = Column(String(200), unique=True, nullable=True, index=True, comment="Microsoft用户ID")
    dingtalk_unionid = Column(String(200), unique=True, nullable=True, index=True, comment="钉钉UnionID")
    dingtalk_userid = Column(String(200), unique=True, nullable=True, index=True, comment="钉钉用户UserID")
    feishu_union_id = Column(String(200), unique=True, nullable=True, index=True, comment="飞书UnionID")
    feishu_userid = Column(String(200), unique=True, nullable=True, index=True, comment="飞书用户OpenID")
    wecom_userid = Column(String(200), unique=True, nullable=True, index=True, comment="企业微信UserID")
    
    # 关系定义（使用primaryjoin指定逻辑关联，lazy='selectin'支持异步加载）
    dept = relationship("Dept", foreign_keys="User.dept_id", primaryjoin="User.dept_id == Dept.id", backref="users", lazy="selectin")
    post = relationship("Post", foreign_keys="User.post_id", primaryjoin="User.post_id == Post.id", lazy="selectin")
    manager = relationship("User", remote_side="User.id", foreign_keys="User.manager_id", primaryjoin="User.manager_id == User.id", backref="subordinates", lazy="selectin")
    
    def __repr__(self):
        return f"<User {self.name or self.username} ({self.username})>"
    
    def get_user_type_display(self) -> str:
        """获取用户类型的显示名称"""
        type_map = {0: "系统用户", 1: "普通用户", 2: "外部用户"}
        return type_map.get(self.user_type, "未知")
    
    def get_user_status_display(self) -> str:
        """获取用户状态的显示名称"""
        status_map = {0: "禁用", 1: "正常", 2: "锁定"}
        return status_map.get(self.user_status, "未知")
    
    def get_gender_display(self) -> str:
        """获取性别的显示名称"""
        gender_map = {0: "未知", 1: "男", 2: "女"}
        return gender_map.get(self.gender, "未知")
    
    def is_active_user(self) -> bool:
        """判断用户是否为正常状态"""
        return self.user_status == 1
    
    def is_locked(self) -> bool:
        """判断用户是否被锁定"""
        return self.user_status == 2
    
    def is_disabled(self) -> bool:
        """判断用户是否被禁用"""
        return self.user_status == 0
    
    def can_delete(self) -> bool:
        """判断用户是否可以删除（系统用户和超级管理员不能删除）"""
        return self.user_type != 0 and not self.is_superuser
