from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator

from app.base_schema import CSTDatetime


class FieldPermissionBase(BaseModel):
    """字段权限基础 Schema"""
    field_name: str
    permission_type: str = "read"  # read/write/hidden/masked
    mask_rule: Optional[str] = None

    @field_validator('permission_type')
    @classmethod
    def validate_permission_type(cls, v):
        allowed = ['read', 'write', 'hidden', 'masked']
        if v not in allowed:
            raise ValueError(f'permission_type must be one of {allowed}')
        return v

    @field_validator('mask_rule')
    @classmethod
    def validate_mask_rule(cls, v, info):
        if info.data.get('permission_type') == 'masked' and not v:
            raise ValueError('mask_rule is required when permission_type is masked')
        if v:
            allowed = ['phone', 'email', 'id_card', 'name', 'default']
            if v not in allowed:
                raise ValueError(f'mask_rule must be one of {allowed}')
        return v


class FieldPermissionCreate(FieldPermissionBase):
    """创建字段权限配置"""
    role_id: str
    resource_type: str


class FieldPermissionUpdate(BaseModel):
    """更新字段权限配置"""
    permission_type: Optional[str] = None
    mask_rule: Optional[str] = None


class FieldPermissionResponse(FieldPermissionBase):
    """字段权限配置响应"""
    id: str
    role_id: str
    resource_type: str
    sort: int = 0
    is_deleted: bool = False
    sys_create_datetime: Optional[CSTDatetime] = None
    sys_update_datetime: Optional[CSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)


class FieldPermissionBatchUpdate(BaseModel):
    """批量更新字段权限配置"""
    role_id: str
    resource_type: str
    configs: List[FieldPermissionBase]


class ResourceFieldMetadata(BaseModel):
    """资源字段元数据"""
    field_name: str
    label: str
    field_type: str  # string/integer/boolean/datetime
    required: bool = False  # 是否必填字段（必填字段不可隐藏）
    sensitive: bool = False  # 是否敏感字段
    maskable: bool = False  # 是否可脱敏
    default_permission: str = "write"


class ResourceFieldsMetadataResponse(BaseModel):
    """资源字段元数据响应"""
    resource_type: str
    display_name: str
    fields: List[ResourceFieldMetadata]
