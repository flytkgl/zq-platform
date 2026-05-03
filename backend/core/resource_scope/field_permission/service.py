from typing import List, Dict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.resource_scope.field_permission.model import ResourceFieldPermissionConfig
from core.resource_scope.field_permission.schema import (
    FieldPermissionCreate,
    FieldPermissionUpdate,
    FieldPermissionBatchUpdate
)


class ResourceFieldPermissionService(BaseService[
    ResourceFieldPermissionConfig,
    FieldPermissionCreate,
    FieldPermissionUpdate
]):
    """资源字段权限配置服务"""

    model = ResourceFieldPermissionConfig

    @classmethod
    async def get_by_role_and_resource(
        cls,
        db: AsyncSession,
        role_id: str,
        resource_type: str
    ) -> List[ResourceFieldPermissionConfig]:
        """获取角色在指定资源类型下的字段权限配置"""
        stmt = select(cls.model).where(
            cls.model.role_id == role_id,
            cls.model.resource_type == resource_type,
            cls.model.is_deleted == False
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_by_roles_and_resource(
        cls,
        db: AsyncSession,
        role_ids: List[str],
        resource_type: str
    ) -> List[ResourceFieldPermissionConfig]:
        """获取多个角色在指定资源类型下的字段权限配置"""
        stmt = select(cls.model).where(
            cls.model.role_id.in_(role_ids),
            cls.model.resource_type == resource_type,
            cls.model.is_deleted == False
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def batch_update(
        cls,
        db: AsyncSession,
        data: FieldPermissionBatchUpdate
    ) -> None:
        """批量更新字段权限配置"""
        from app.field_permission_cache import FieldPermissionCache
        
        # 1. 删除该角色在该资源类型下的所有字段权限配置
        stmt = delete(cls.model).where(
            cls.model.role_id == data.role_id,
            cls.model.resource_type == data.resource_type
        )
        await db.execute(stmt)

        # 2. 批量插入新的配置
        for config in data.configs:
            new_config = cls.model(
                role_id=data.role_id,
                resource_type=data.resource_type,
                field_name=config.field_name,
                permission_type=config.permission_type,
                mask_rule=config.mask_rule
            )
            db.add(new_config)

        await db.commit()
        
        # 3. 清除缓存
        await FieldPermissionCache.delete(data.role_id, data.resource_type)
        # 清除包含该角色的所有多角色缓存
        await FieldPermissionCache.delete_by_role(data.role_id)

    @classmethod
    async def merge_field_permissions(
        cls,
        configs: List[ResourceFieldPermissionConfig],
        strategy: str = "most_permissive"
    ) -> Dict[str, Dict]:
        """
        合并多个角色的字段权限配置
        
        Args:
            configs: 字段权限配置列表
            strategy: 合并策略
                - most_permissive: 最宽松（默认）
                - most_restrictive: 最严格
        
        Returns:
            合并后的字段权限字典
        """
        field_perms = {}

        # 权限等级定义（数字越大权限越高）
        perm_levels = {
            'hidden': 0,
            'masked': 1,
            'read': 2,
            'write': 3
        }

        for config in configs:
            field_name = config.field_name
            current_perm = config.permission_type
            current_level = perm_levels.get(current_perm, 0)

            if field_name not in field_perms:
                field_perms[field_name] = {
                    'permission': current_perm,
                    'mask_rule': config.mask_rule,
                    'level': current_level
                }
            else:
                existing_level = field_perms[field_name]['level']

                if strategy == "most_permissive":
                    # 取权限最高的
                    if current_level > existing_level:
                        field_perms[field_name] = {
                            'permission': current_perm,
                            'mask_rule': config.mask_rule,
                            'level': current_level
                        }
                elif strategy == "most_restrictive":
                    # 取权限最低的
                    if current_level < existing_level:
                        field_perms[field_name] = {
                            'permission': current_perm,
                            'mask_rule': config.mask_rule,
                            'level': current_level
                        }

        # 移除临时的 level 字段
        for field_name in field_perms:
            del field_perms[field_name]['level']

        return field_perms
