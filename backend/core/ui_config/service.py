#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI Config Service - UI配置服务层
"""
import json
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.base_service import BaseService
from core.ui_config.model import UIConfig
from core.ui_config.schema import UIConfigCreate, UIConfigUpdate


class UIConfigService(BaseService[UIConfig, UIConfigCreate, UIConfigUpdate]):
    """
    UI配置服务层
    继承BaseService，自动获得增删改查功能
    """
    
    model = UIConfig
    
    @classmethod
    async def get_by_key(
        cls, 
        db: AsyncSession, 
        config_key: str, 
        application_id: Optional[str] = None
    ) -> Optional[UIConfig]:
        """
        根据配置键获取配置
        
        :param db: 数据库会话
        :param config_key: 配置键
        :param application_id: 应用ID，None表示主应用配置
        """
        query = select(UIConfig).where(
            UIConfig.config_key == config_key,
            UIConfig.is_deleted == False  # noqa: E712
        )
        if application_id:
            query = query.where(UIConfig.application_id == application_id)
        else:
            query = query.where(UIConfig.application_id.is_(None))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_type(cls, db: AsyncSession, config_type: str) -> List[UIConfig]:
        """根据配置类型获取配置列表"""
        result = await db.execute(
            select(UIConfig).where(
                UIConfig.config_type == config_type,
                UIConfig.status == True,  # noqa: E712
                UIConfig.is_deleted == False  # noqa: E712
            ).order_by(UIConfig.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_all_active(cls, db: AsyncSession) -> List[UIConfig]:
        """获取所有启用的配置"""
        result = await db.execute(
            select(UIConfig).where(
                UIConfig.status == True,  # noqa: E712
                UIConfig.is_deleted == False  # noqa: E712
            ).order_by(UIConfig.sort)
        )
        return list(result.scalars().all())
    
    @classmethod
    async def get_preferences_config(
        cls, 
        db: AsyncSession, 
        application_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取前端偏好配置
        返回格式与前端 Preferences 类型一致
        
        :param db: 数据库会话
        :param application_id: 应用ID，None表示主应用配置
        """
        config = await cls.get_by_key(db, "frontend_preferences", application_id)
        
        if config and config.config_value and config.status:
            try:
                return json.loads(config.config_value)
            except json.JSONDecodeError:
                return None
        
        # 如果子应用没有配置，回退到主应用配置
        if application_id:
            return await cls.get_preferences_config(db, None)
        
        return None
    
    @classmethod
    async def update_preferences_config(
        cls,
        db: AsyncSession,
        preferences: Dict[str, Any],
        application_id: Optional[str] = None
    ) -> UIConfig:
        """
        更新前端偏好配置
        如果不存在则创建
        
        :param db: 数据库会话
        :param preferences: 偏好配置
        :param application_id: 应用ID，None表示主应用配置
        """
        config = await cls.get_by_key(db, "frontend_preferences", application_id)
        config_value = json.dumps(preferences, ensure_ascii=False)
        
        if config:
            config.config_value = config_value
            await db.commit()
            await db.refresh(config)
            return config
        else:
            new_config = UIConfig(
                application_id=application_id,
                config_key="frontend_preferences",
                config_value=config_value,
                config_type="preferences",
                description="前端UI偏好配置" if not application_id else f"子应用UI偏好配置",
                status=True
            )
            db.add(new_config)
            await db.commit()
            await db.refresh(new_config)
            return new_config
    
    @classmethod
    async def update_value_by_key(
        cls,
        db: AsyncSession,
        config_key: str,
        config_value: str
    ) -> Optional[UIConfig]:
        """根据配置键更新配置值"""
        config = await cls.get_by_key(db, config_key)
        if config:
            config.config_value = config_value
            await db.commit()
            await db.refresh(config)
            return config
        return None
    
    @classmethod
    async def get_config_value(cls, db: AsyncSession, config_key: str) -> Optional[Any]:
        """获取配置值（解析JSON）"""
        config = await cls.get_by_key(db, config_key)
        if config and config.config_value:
            try:
                return json.loads(config.config_value)
            except json.JSONDecodeError:
                return config.config_value
        return None
