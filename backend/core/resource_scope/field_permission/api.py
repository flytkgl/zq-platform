from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.base_schema import ResponseModel
from app.resource_registry import ResourceRegistry
from core.resource_scope.field_permission.schema import (
    FieldPermissionResponse,
    FieldPermissionBatchUpdate,
    ResourceFieldsMetadataResponse,
    ResourceFieldMetadata
)
from core.resource_scope.field_permission.service import ResourceFieldPermissionService

router = APIRouter(prefix="/field-permissions", tags=["字段权限配置"])


@router.get("/resource-fields", response_model=List[ResourceFieldsMetadataResponse], summary="获取所有资源的字段元数据")
async def get_all_resource_fields(
    application_id: Optional[str] = Query(None, alias="applicationId", description="应用ID，子应用访问时只显示该应用的资源")
):
    """获取所有已注册资源的字段元数据"""
    # 获取资源列表，支持按应用过滤
    all_resources = ResourceRegistry.get_all_resources(application_id=application_id)
    result = []

    for resource_item in all_resources:
        resource_type = resource_item['resource_type']
        resource_info = ResourceRegistry.get_resource(resource_type)
        if not resource_info:
            continue
        
        # 优先从 service_class 获取字段元数据，否则从注册表获取
        field_metadata = None
        service_class = resource_info.get('service')
        if service_class and hasattr(service_class, 'FIELD_METADATA'):
            field_metadata = service_class.FIELD_METADATA
        elif resource_info.get('field_metadata'):
            field_metadata = resource_info.get('field_metadata')
        
        if not field_metadata:
            continue
        fields = [
            ResourceFieldMetadata(
                field_name=field_name,
                label=meta.get('label', field_name),
                field_type=meta.get('field_type', 'string'),
                required=meta.get('required', False),
                sensitive=meta.get('sensitive', False),
                maskable=meta.get('maskable', False),
                default_permission=meta.get('default_permission', 'write')
            )
            for field_name, meta in field_metadata.items()
        ]

        result.append(ResourceFieldsMetadataResponse(
            resource_type=resource_type,
            display_name=resource_info.get('display_name', resource_type),
            fields=fields
        ))

    return result


@router.get("/resource-fields/{resource_type}", response_model=ResourceFieldsMetadataResponse, summary="获取指定资源的字段元数据")
async def get_resource_fields(resource_type: str):
    """获取指定资源的字段元数据"""
    resource_info = ResourceRegistry.get_resource(resource_type)
    if not resource_info:
        raise HTTPException(status_code=404, detail=f"资源类型不存在: {resource_type}")

    # 优先从 service_class 获取字段元数据，否则从注册表获取
    field_metadata = None
    service_class = resource_info.get('service')
    if service_class and hasattr(service_class, 'FIELD_METADATA'):
        field_metadata = service_class.FIELD_METADATA
    elif resource_info.get('field_metadata'):
        field_metadata = resource_info.get('field_metadata')
    
    if not field_metadata:
        raise HTTPException(status_code=404, detail=f"资源未定义字段元数据: {resource_type}")

    fields = [
        ResourceFieldMetadata(
            field_name=field_name,
            label=meta.get('label', field_name),
            field_type=meta.get('field_type', 'string'),
            required=meta.get('required', False),
            sensitive=meta.get('sensitive', False),
            maskable=meta.get('maskable', False),
            default_permission=meta.get('default_permission', 'write')
        )
        for field_name, meta in field_metadata.items()
    ]

    return ResourceFieldsMetadataResponse(
        resource_type=resource_type,
        display_name=resource_info.get('display_name', resource_type),
        fields=fields
    )


@router.get("/{role_id}", response_model=List[FieldPermissionResponse], summary="获取角色的字段权限配置")
async def get_role_field_permissions(
    role_id: str,
    resource_type: str = Query(..., description="资源类型"),
    db: AsyncSession = Depends(get_db)
):
    """获取角色在指定资源类型下的字段权限配置"""
    configs = await ResourceFieldPermissionService.get_by_role_and_resource(
        db, role_id, resource_type
    )
    return configs


@router.post("/batch", response_model=ResponseModel, summary="批量更新字段权限配置")
async def batch_update_field_permissions(
    data: FieldPermissionBatchUpdate,
    db: AsyncSession = Depends(get_db)
):
    """批量更新角色的字段权限配置"""
    # 验证资源类型是否存在
    if not ResourceRegistry.validate_resource_type(data.resource_type):
        raise HTTPException(status_code=400, detail=f"资源类型不存在: {data.resource_type}")

    await ResourceFieldPermissionService.batch_update(db, data)
    return ResponseModel(message="字段权限配置成功")


@router.delete("/{role_id}", response_model=ResponseModel, summary="删除角色的字段权限配置")
async def delete_role_field_permissions(
    role_id: str,
    resource_type: str = Query(..., description="资源类型"),
    db: AsyncSession = Depends(get_db)
):
    """删除角色在指定资源类型下的所有字段权限配置"""
    from sqlalchemy import delete
    from core.resource_scope.field_permission.model import ResourceFieldPermissionConfig

    stmt = delete(ResourceFieldPermissionConfig).where(
        ResourceFieldPermissionConfig.role_id == role_id,
        ResourceFieldPermissionConfig.resource_type == resource_type
    )
    await db.execute(stmt)
    await db.commit()

    return ResponseModel(message="删除成功")
