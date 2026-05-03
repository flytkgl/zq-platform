#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SystemConfig Service - 系统配置服务层
"""
from typing import Dict, Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from app.config_manager import config_manager, GROUP_ENV_MAPPING, SECRET_KEYS
from core.system_config.model import SystemConfig
from core.system_config.schema import SystemConfigCreate, SystemConfigUpdate


class SystemConfigService(BaseService[SystemConfig, SystemConfigCreate, SystemConfigUpdate]):
    """系统配置服务层"""

    model = SystemConfig

    @classmethod
    async def get_group_config(cls, group: str, mask_secrets: bool = True) -> Dict[str, Any]:
        """
        获取分组配置（通过 config_manager 三级获取）

        :param group: 配置分组
        :param mask_secrets: 是否对敏感字段脱敏
        :return: {key: value} 字典
        """
        configs = await config_manager.get_group(group)

        if mask_secrets:
            return {
                k: config_manager.mask_value(v) if config_manager.is_secret_key(k) and v else v
                for k, v in configs.items()
            }
        return configs

    @classmethod
    async def update_group_config(
        cls,
        db: AsyncSession,
        group: str,
        configs: Dict[str, Optional[str]],
    ) -> Dict[str, Any]:
        """
        批量更新分组配置

        :param db: 数据库会话
        :param group: 配置分组
        :param configs: {key: value} 字典
        :return: 更新后的配置（脱敏）
        """
        for key, value in configs.items():
            # 如果敏感字段传入的是脱敏值（含 ***），跳过不更新
            if config_manager.is_secret_key(key) and value and "***" in value:
                continue

            result = await db.execute(
                select(SystemConfig).where(
                    SystemConfig.config_group == group,
                    SystemConfig.config_key == key,
                    SystemConfig.is_deleted == False,  # noqa: E712
                )
            )
            config = result.scalar_one_or_none()

            if config:
                config.config_value = value
            else:
                config = SystemConfig(
                    config_group=group,
                    config_key=key,
                    config_value=value,
                    is_secret=key in SECRET_KEYS,
                    status=True,
                )
                db.add(config)

        await db.commit()

        # 清除该分组的 Redis 缓存
        await config_manager.invalidate_group(group)

        # 返回更新后的配置（脱敏）
        return await cls.get_group_config(group, mask_secrets=True)

    @classmethod
    async def get_all_groups_config(cls, mask_secrets: bool = True) -> Dict[str, Dict[str, Any]]:
        """获取所有分组配置"""
        result = {}
        for group in GROUP_ENV_MAPPING:
            result[group] = await cls.get_group_config(group, mask_secrets=mask_secrets)
        return result

    @classmethod
    async def get_group_db_records(cls, db: AsyncSession, group: str) -> List[SystemConfig]:
        """获取分组在数据库中的记录"""
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.config_group == group,
                SystemConfig.is_deleted == False,  # noqa: E712
            ).order_by(SystemConfig.sort)
        )
        return list(result.scalars().all())

    @classmethod
    async def delete_group_config(cls, db: AsyncSession, group: str) -> bool:
        """删除分组配置（软删除）"""
        result = await db.execute(
            select(SystemConfig).where(
                SystemConfig.config_group == group,
                SystemConfig.is_deleted == False,  # noqa: E712
            )
        )
        configs = list(result.scalars().all())
        for config in configs:
            config.is_deleted = True
        await db.commit()

        # 清除缓存
        await config_manager.invalidate_group(group)
        return len(configs) > 0
