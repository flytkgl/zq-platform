#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
存储后端 - 支持本地存储、阿里云OSS、Minio、Azure Blob
"""
import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import BinaryIO, Tuple, Optional

from app.config import settings


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def save(self, file: BinaryIO, filename: str, folder_path: str = '') -> Tuple[str, str]:
        """
        保存文件
        :param file: 文件对象
        :param filename: 文件名
        :param folder_path: 文件夹路径
        :return: (存储路径, 访问URL)
        """
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    def get_url(self, file_path: str) -> str:
        """获取文件访问URL"""
        pass

    @abstractmethod
    def get_size(self, file_path: str) -> int:
        """获取文件大小"""
        pass

    def calculate_md5(self, file: BinaryIO) -> str:
        """计算文件MD5"""
        md5_hash = hashlib.md5()
        file.seek(0)
        for chunk in iter(lambda: file.read(4096), b""):
            md5_hash.update(chunk)
        file.seek(0)
        return md5_hash.hexdigest()

    def generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名（使用UUID，防止路径可预测）"""
        import uuid
        name, ext = os.path.splitext(original_filename)
        return f"{uuid.uuid4().hex}{ext}"


class LocalStorageBackend(StorageBackend):
    """本地存储后端"""

    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.join(os.getcwd(), 'media', 'file_manager')
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, file: BinaryIO, filename: str, folder_path: str = '') -> Tuple[str, str]:
        # 生成唯一文件名
        unique_filename = self.generate_filename(filename)

        # 构建完整路径
        relative_path = os.path.join(folder_path, unique_filename).replace('\\', '/')
        full_path = os.path.join(self.base_path, relative_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(full_path) if os.path.dirname(full_path) else self.base_path, exist_ok=True)

        # 保存文件
        with open(full_path, 'wb') as destination:
            if hasattr(file, 'read'):
                # 文件对象
                chunk = file.read(8192)
                while chunk:
                    destination.write(chunk)
                    chunk = file.read(8192)
            else:
                # 字节数据
                destination.write(file)

        # 返回相对路径和URL
        url = relative_path
        return relative_path, url

    def delete(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_path, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def exists(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_path, file_path)
        return os.path.exists(full_path)

    def get_url(self, file_path: str) -> str:
        return f"/api/file_manager/file/download?path={file_path}"

    def get_size(self, file_path: str) -> int:
        full_path = os.path.join(self.base_path, file_path)
        return os.path.getsize(full_path) if os.path.exists(full_path) else 0

    def get_full_path(self, file_path: str) -> str:
        """获取文件完整路径"""
        return os.path.join(self.base_path, file_path)


class OSSStorageBackend(StorageBackend):
    """阿里云OSS存储后端"""

    def __init__(self, endpoint: str, access_key_id: str, access_key_secret: str, bucket_name: str):
        self.endpoint = endpoint
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket_name = bucket_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import oss2
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self._client = oss2.Bucket(auth, self.endpoint, self.bucket_name)
        return self._client

    def save(self, file: BinaryIO, filename: str, folder_path: str = '') -> Tuple[str, str]:
        unique_filename = self.generate_filename(filename)
        key = os.path.join('file_manager', folder_path, unique_filename).replace('\\', '/')

        # 上传文件
        self.client.put_object(key, file)

        # 生成URL
        url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '').replace('http://', '')}/{key}"
        return key, url

    def delete(self, file_path: str) -> bool:
        try:
            self.client.delete_object(file_path)
            return True
        except Exception:
            return False

    def exists(self, file_path: str) -> bool:
        try:
            self.client.head_object(file_path)
            return True
        except:
            return False

    def get_url(self, file_path: str) -> str:
        return f"https://{self.bucket_name}.{self.endpoint.replace('https://', '').replace('http://', '')}/{file_path}"

    def get_size(self, file_path: str) -> int:
        try:
            result = self.client.head_object(file_path)
            return result.content_length
        except:
            return 0


class MinioStorageBackend(StorageBackend):
    """Minio存储后端"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str, secure: bool = False):
        # 处理endpoint，确保没有协议前缀
        if endpoint.startswith('http://'):
            endpoint = endpoint[7:]
            secure = False
        elif endpoint.startswith('https://'):
            endpoint = endpoint[8:]
            secure = True

        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from minio import Minio
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
        return self._client

    def save(self, file: BinaryIO, filename: str, folder_path: str = '') -> Tuple[str, str]:
        unique_filename = self.generate_filename(filename)
        object_name = os.path.join('file_manager', folder_path, unique_filename).replace('\\', '/')

        # 获取文件大小
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        # 上传文件
        self.client.put_object(
            self.bucket_name,
            object_name,
            file,
            file_size
        )

        # 生成URL
        url = f"{self.bucket_name}/{object_name}"
        return object_name, url

    def delete(self, file_path: str) -> bool:
        try:
            self.client.remove_object(self.bucket_name, file_path)
            return True
        except Exception:
            return False

    def exists(self, file_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, file_path)
            return True
        except:
            return False

    def get_url(self, file_path: str) -> str:
        protocol = 'https' if self.secure else 'http'
        return f"{protocol}://{self.endpoint}/{self.bucket_name}/{file_path}"

    def get_size(self, file_path: str) -> int:
        try:
            result = self.client.stat_object(self.bucket_name, file_path)
            return result.size
        except:
            return 0

    def get_presigned_url(self, file_path: str, expires: timedelta = None) -> str:
        """获取预签名临时URL"""
        if expires is None:
            expires = timedelta(hours=1)

        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                file_path,
                expires=expires
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def get_presigned_upload_url(self, file_path: str, expires: timedelta = None) -> str:
        """获取预签名上传URL"""
        if expires is None:
            expires = timedelta(hours=1)

        try:
            url = self.client.presigned_put_object(
                self.bucket_name,
                file_path,
                expires=expires
            )
            return url
        except Exception as e:
            raise Exception(f"Failed to generate presigned upload URL: {str(e)}")

    def get_file_content(self, file_path: str):
        """获取文件内容"""
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            return response
        except Exception as e:
            raise Exception(f"Failed to get file content: {str(e)}")

    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            stat = self.client.stat_object(self.bucket_name, file_path)
            return {
                'size': stat.size,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'metadata': stat.metadata
            }
        except Exception as e:
            raise Exception(f"Failed to get file info: {str(e)}")


class AzureBlobStorageBackend(StorageBackend):
    """Azure Blob存储后端"""

    def __init__(self, account_name: str, account_key: str, container_name: str):
        self.account_name = account_name
        self.account_key = account_key
        self.container_name = container_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from azure.storage.blob import BlobServiceClient
            connection_string = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};AccountKey={self.account_key};EndpointSuffix=core.windows.net"
            self._client = BlobServiceClient.from_connection_string(connection_string)

            # 确保容器存在
            container_client = self._client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
        return self._client

    def save(self, file: BinaryIO, filename: str, folder_path: str = '') -> Tuple[str, str]:
        unique_filename = self.generate_filename(filename)
        blob_name = os.path.join('file_manager', folder_path, unique_filename).replace('\\', '/')

        # 获取blob客户端
        blob_client = self.client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        # 上传文件
        blob_client.upload_blob(file, overwrite=True)

        # 生成URL
        url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
        return blob_name, url

    def delete(self, file_path: str) -> bool:
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=file_path
            )
            blob_client.delete_blob()
            return True
        except Exception:
            return False

    def exists(self, file_path: str) -> bool:
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=file_path
            )
            blob_client.get_blob_properties()
            return True
        except:
            return False

    def get_url(self, file_path: str) -> str:
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{file_path}"

    def get_size(self, file_path: str) -> int:
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=file_path
            )
            properties = blob_client.get_blob_properties()
            return properties.size
        except:
            return 0


def get_storage_backend(config: dict = None) -> StorageBackend:
    """获取存储后端实例"""
    if config is None:
        # 从配置文件读取默认配置
        config = {
            'storage_type': getattr(settings, 'FILE_STORAGE_TYPE', 'local'),
            'local_base_path': getattr(settings, 'FILE_STORAGE_LOCAL_PATH', None),
            'oss_endpoint': getattr(settings, 'OSS_ENDPOINT', None),
            'oss_access_key_id': getattr(settings, 'OSS_ACCESS_KEY_ID', None),
            'oss_access_key_secret': getattr(settings, 'OSS_ACCESS_KEY_SECRET', None),
            'oss_bucket_name': getattr(settings, 'OSS_BUCKET_NAME', None),
            'minio_endpoint': getattr(settings, 'MINIO_ENDPOINT', None),
            'minio_access_key': getattr(settings, 'MINIO_ACCESS_KEY', None),
            'minio_secret_key': getattr(settings, 'MINIO_SECRET_KEY', None),
            'minio_bucket_name': getattr(settings, 'MINIO_BUCKET_NAME', None),
            'minio_secure': getattr(settings, 'MINIO_SECURE', False),
            'azure_account_name': getattr(settings, 'AZURE_ACCOUNT_NAME', None),
            'azure_account_key': getattr(settings, 'AZURE_ACCOUNT_KEY', None),
            'azure_container_name': getattr(settings, 'AZURE_CONTAINER_NAME', None),
        }

    storage_type = config.get('storage_type', 'local')

    if storage_type == 'local':
        return LocalStorageBackend(config.get('local_base_path'))
    elif storage_type == 'oss':
        return OSSStorageBackend(
            config['oss_endpoint'],
            config['oss_access_key_id'],
            config['oss_access_key_secret'],
            config['oss_bucket_name']
        )
    elif storage_type == 'minio':
        return MinioStorageBackend(
            config['minio_endpoint'],
            config['minio_access_key'],
            config['minio_secret_key'],
            config['minio_bucket_name'],
            config.get('minio_secure', False)
        )
    elif storage_type == 'azure':
        return AzureBlobStorageBackend(
            config['azure_account_name'],
            config['azure_account_key'],
            config['azure_container_name']
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
