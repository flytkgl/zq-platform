#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件管理Schema
"""
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, ConfigDict, Field

from app.base_schema import CSTDatetime


# ==================== 文件管理 Schema ====================

class FileManagerBase(BaseModel):
    """文件管理基础Schema"""
    name: str = Field(..., description="文件/文件夹名称")
    type: str = Field(default='file', description="类型: file/folder")
    parent_id: Optional[str] = Field(None, description="父文件夹ID")
    is_public: bool = Field(default=False, description="是否公开")


class FileManagerCreate(FileManagerBase):
    """创建文件记录Schema（内部使用）"""
    path: str = Field(default='', description="文件路径")
    size: int = Field(default=0, description="文件大小")
    file_ext: Optional[str] = Field(None, description="文件扩展名")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    storage_type: str = Field(default='local', description="存储类型")
    storage_path: str = Field(default='', description="存储路径")
    url: Optional[str] = Field(None, description="访问URL")
    md5: Optional[str] = Field(None, description="文件MD5")


class FileManagerUpdate(BaseModel):
    """更新文件记录Schema"""
    name: Optional[str] = None
    is_public: Optional[bool] = None


class FileManagerResponse(BaseModel):
    """文件管理响应Schema"""
    id: str
    name: str
    type: str = Field(alias="file_type")
    parent_id: Optional[str] = None
    parent_name: Optional[str] = None
    path: str
    size: int = Field(alias="file_size")
    file_ext: Optional[str] = None
    mime_type: Optional[str] = None
    storage_type: str
    storage_path: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    md5: Optional[str] = None
    is_public: bool
    download_count: int
    is_system: bool = False
    source: Optional[str] = None
    sys_creator_id: Optional[str] = None
    has_children: bool = False
    updated_time: Optional[str] = None
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FileManagerSimpleResponse(BaseModel):
    """文件管理简单响应Schema"""
    id: str
    name: str
    type: str
    size: int
    sys_create_datetime: Optional[CSTDatetime] = None
    mime_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== 文件夹操作 Schema ====================

class CreateFolderIn(BaseModel):
    """创建文件夹输入Schema"""
    name: str = Field(..., description="文件夹名称")
    parent_id: Optional[str] = Field(None, alias="parentId", description="父文件夹ID")

    model_config = ConfigDict(populate_by_name=True)


class MoveItemsIn(BaseModel):
    """移动文件/文件夹输入Schema"""
    ids: List[str] = Field(..., description="要移动的文件/文件夹ID列表")
    target_folder_id: Optional[str] = Field(None, alias="targetFolderId", description="目标文件夹ID")

    model_config = ConfigDict(populate_by_name=True)


class RenameItemIn(BaseModel):
    """重命名输入Schema"""
    name: str = Field(..., description="新名称")


class BatchDeleteIn(BaseModel):
    """批量删除输入Schema"""
    ids: List[str] = Field(..., description="要删除的文件/文件夹ID列表")


# ==================== 存储配置 Schema ====================

class FileStorageConfigResponse(BaseModel):
    """文件存储配置响应Schema"""
    storage_type: str = Field(default='local', alias="storageType", description="存储类型")
    local_base_path: Optional[str] = Field(None, alias="localBasePath", description="本地存储路径")
    oss_endpoint: Optional[str] = Field(None, alias="ossEndpoint", description="OSS端点")
    oss_access_key_id: Optional[str] = Field(None, alias="ossAccessKeyId", description="OSS访问密钥ID")
    oss_bucket_name: Optional[str] = Field(None, alias="ossBucketName", description="OSS存储桶名称")
    minio_endpoint: Optional[str] = Field(None, alias="minioEndpoint", description="Minio端点")
    minio_bucket_name: Optional[str] = Field(None, alias="minioBucketName", description="Minio存储桶名称")
    azure_account_name: Optional[str] = Field(None, alias="azureAccountName", description="Azure存储账户名称")
    azure_container_name: Optional[str] = Field(None, alias="azureContainerName", description="Azure容器名称")

    model_config = ConfigDict(populate_by_name=True)


class FileStorageConfigUpdate(BaseModel):
    """更新存储配置Schema"""
    storage_type: str = Field(default='local', alias="storageType", description="存储类型")
    local_base_path: Optional[str] = Field(None, alias="localBasePath")
    oss_endpoint: Optional[str] = Field(None, alias="ossEndpoint")
    oss_access_key_id: Optional[str] = Field(None, alias="ossAccessKeyId")
    oss_access_key_secret: Optional[str] = Field(None, alias="ossAccessKeySecret")
    oss_bucket_name: Optional[str] = Field(None, alias="ossBucketName")
    minio_endpoint: Optional[str] = Field(None, alias="minioEndpoint")
    minio_access_key: Optional[str] = Field(None, alias="minioAccessKey")
    minio_secret_key: Optional[str] = Field(None, alias="minioSecretKey")
    minio_bucket_name: Optional[str] = Field(None, alias="minioBucketName")
    azure_account_name: Optional[str] = Field(None, alias="azureAccountName")
    azure_account_key: Optional[str] = Field(None, alias="azureAccountKey")
    azure_container_name: Optional[str] = Field(None, alias="azureContainerName")

    model_config = ConfigDict(populate_by_name=True)


# ==================== 分块上传 Schema ====================

class InitChunkUploadIn(BaseModel):
    """初始化分块上传输入Schema"""
    filename: str = Field(..., description="文件名")
    total_size: int = Field(..., alias="totalSize", description="文件总大小（字节）")
    chunk_size: int = Field(default=5 * 1024 * 1024, alias="chunkSize", description="分块大小（字节），默认5MB")
    parent_id: Optional[str] = Field(None, alias="parentId", description="父文件夹ID")
    is_public: bool = Field(default=False, alias="isPublic", description="是否公开")
    file_hash: Optional[str] = Field(None, alias="fileHash", description="文件MD5哈希，用于秒传")

    model_config = ConfigDict(populate_by_name=True)


class InitChunkUploadOut(BaseModel):
    """初始化分块上传输出Schema"""
    upload_id: str = Field(..., alias="uploadId", description="上传ID")
    chunk_size: int = Field(..., alias="chunkSize", description="分块大小")
    total_chunks: int = Field(..., alias="totalChunks", description="总分块数")
    uploaded_chunks: List[int] = Field(default=[], alias="uploadedChunks", description="已上传的分块索引列表")
    file_exists: bool = Field(default=False, alias="fileExists", description="文件是否已存在（秒传）")
    file_id: Optional[str] = Field(None, alias="fileId", description="如果文件已存在，返回文件ID")

    model_config = ConfigDict(populate_by_name=True)


class UploadChunkOut(BaseModel):
    """上传分块输出Schema"""
    chunk_index: int = Field(..., alias="chunkIndex", description="分块索引")
    uploaded: bool = Field(..., description="是否上传成功")

    model_config = ConfigDict(populate_by_name=True)


class MergeChunksIn(BaseModel):
    """合并分块输入Schema"""
    upload_id: str = Field(..., alias="uploadId", description="上传ID")

    model_config = ConfigDict(populate_by_name=True)


class ChunkUploadStatusOut(BaseModel):
    """分块上传状态输出Schema"""
    upload_id: str = Field(..., alias="uploadId", description="上传ID")
    filename: str = Field(..., description="文件名")
    total_size: int = Field(..., alias="totalSize", description="文件总大小")
    total_chunks: int = Field(..., alias="totalChunks", description="总分块数")
    uploaded_chunks: List[int] = Field(..., alias="uploadedChunks", description="已上传的分块索引")
    completed: bool = Field(..., description="是否完成上传")

    model_config = ConfigDict(populate_by_name=True)


# ==================== 文件URL Schema ====================

class FileUrlResponse(BaseModel):
    """文件URL响应Schema"""
    url: str = Field(..., description="文件访问URL")


class BatchFileUrlsResponse(BaseModel):
    """批量文件URL响应Schema"""
    urls: dict = Field(..., description="文件ID到URL的映射")


# ==================== 临时访问令牌 Schema ====================

class CreateAccessTokenIn(BaseModel):
    """创建临时访问令牌输入Schema"""
    file_id: str = Field(..., alias="fileId", description="文件ID")
    expires_in: int = Field(default=3600, alias="expiresIn", description="过期时间（秒），默认1小时")

    model_config = ConfigDict(populate_by_name=True)


class AccessTokenResponse(BaseModel):
    """临时访问令牌响应Schema"""
    token: str = Field(..., description="临时访问令牌")
    expires_at: CSTDatetime = Field(..., alias="expiresAt", description="过期时间")
    file_id: str = Field(..., alias="fileId", description="文件ID")

    model_config = ConfigDict(populate_by_name=True)


class AccessTokenUrlResponse(BaseModel):
    """带令牌的文件URL响应Schema"""
    url: str = Field(..., description="带临时令牌的文件访问URL")
    token: str = Field(..., description="临时访问令牌")
    expires_at: CSTDatetime = Field(..., alias="expiresAt", description="过期时间")

    model_config = ConfigDict(populate_by_name=True)


# ==================== AI OCR 识别 Schema ====================

class OcrFieldMapping(BaseModel):
    """OCR字段映射配置"""
    source: str = Field(..., description="Function返回的字段名")
    target: str = Field(..., description="表单字段名")
    transform: Optional[str] = Field(None, description="转换规则")


class OcrSchemaField(BaseModel):
    """OCR结构化输出字段定义（与LLM节点SchemaField一致）"""
    name: str = Field(..., description="字段名")
    type: str = Field(default="string", description="字段类型: string/number/integer/boolean/array/object")
    description: str = Field(default="", description="字段描述")
    required: bool = Field(default=False, description="是否必填")
    items: Optional['OcrSchemaField'] = Field(None, description="array类型的元素定义")
    properties: Optional[List['OcrSchemaField']] = Field(None, description="object类型的子属性")
    enum: Optional[List[str]] = Field(None, description="枚举值（仅string类型）")
    default: Optional[Any] = Field(None, description="默认值")


class OcrRecognizeRequest(BaseModel):
    """OCR智能识别请求Schema"""
    file_id: str = Field(..., alias="fileId", description="文件ID")
    output_schema: Optional[List[OcrSchemaField]] = Field(None, alias="outputSchema", description="结构化输出字段定义")
    prompt: Optional[str] = Field(None, description="自定义提示词")

    model_config = ConfigDict(populate_by_name=True)


class OcrRecognizeResponse(BaseModel):
    """OCR智能识别响应Schema"""
    success: bool = Field(..., description="是否成功")
    raw_text: Optional[str] = Field(None, alias="rawText", description="原始识别文字")
    extracted_data: Optional[dict] = Field(None, alias="extractedData", description="提取的结构化数据")
    error: Optional[str] = Field(None, description="错误信息")

    model_config = ConfigDict(populate_by_name=True)
