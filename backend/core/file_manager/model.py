#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件管理模型
"""
from sqlalchemy import Column, String, Text, Boolean, BigInteger, Integer, ForeignKey, Index

from app.base_model import BaseModel


class FileManager(BaseModel):
    """文件管理模型"""
    __tablename__ = "core_file_manager"

    name = Column(String(255), nullable=False, comment="文件/文件夹名称")
    type = Column(String(10), default='file', comment="类型: file/folder")
    parent_id = Column(String(36), nullable=True, comment="父文件夹ID")
    path = Column(Text, nullable=False, default='', comment="文件路径")
    size = Column(BigInteger, default=0, comment="文件大小(字节)")
    file_ext = Column(String(50), nullable=True, comment="文件扩展名")
    mime_type = Column(String(200), nullable=True, comment="MIME类型")
    storage_type = Column(String(20), default='local', comment="存储类型: local/oss/minio/azure")
    storage_path = Column(Text, nullable=False, default='', comment="存储路径")
    url = Column(Text, nullable=True, comment="访问URL")
    thumbnail_url = Column(Text, nullable=True, comment="缩略图URL")
    md5 = Column(String(32), nullable=True, comment="文件MD5")
    is_public = Column(Boolean, default=False, comment="是否公开")
    download_count = Column(Integer, default=0, comment="下载次数")
    is_system = Column(Boolean, default=False, comment="是否系统文件夹（不可删除/重命名）")
    source = Column(String(50), nullable=True, comment="来源模块标识")

    __table_args__ = (
        Index('ix_file_manager_parent_type', 'parent_id', 'type'),
        Index('ix_file_manager_storage_type', 'storage_type'),
        Index('ix_file_manager_md5', 'md5'),
    )
