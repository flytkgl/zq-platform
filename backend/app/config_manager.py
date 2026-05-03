#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理器 - 三级配置获取工具

优先级: Redis 缓存 → 数据库 → env 配置文件

使用方式:
    from app.config_manager import config_manager

    # 获取单个配置
    value = await config_manager.get("notify_email", "smtp_host")

    # 获取整个分组
    email_config = await config_manager.get_group("notify_email")

    # 设置配置（同时写入数据库和 Redis）
    await config_manager.set("notify_email", "smtp_host", "smtp.qq.com", db=db)
"""
import json
import logging
from typing import Any, Dict, List, Optional

from utils.redis import CacheManager

logger = logging.getLogger(__name__)

# Redis 缓存过期时间（秒），1 小时
CONFIG_CACHE_EXPIRE = 3600

# 配置分组到 env 配置文件字段的映射
# 格式: { "config_group": { "config_key": "SETTINGS_ATTR_NAME" } }
GROUP_ENV_MAPPING: Dict[str, Dict[str, str]] = {
    # ===== OAuth SSO 配置 =====
    "oauth_gitee": {
        "client_id": "GITEE_CLIENT_ID",
        "client_secret": "GITEE_CLIENT_SECRET",
        "redirect_uri": "GITEE_REDIRECT_URI",
    },
    "oauth_github": {
        "client_id": "GITHUB_CLIENT_ID",
        "client_secret": "GITHUB_CLIENT_SECRET",
        "redirect_uri": "GITHUB_REDIRECT_URI",
    },
    "oauth_qq": {
        "app_id": "QQ_APP_ID",
        "app_key": "QQ_APP_KEY",
        "redirect_uri": "QQ_REDIRECT_URI",
    },
    "oauth_google": {
        "client_id": "GOOGLE_CLIENT_ID",
        "client_secret": "GOOGLE_CLIENT_SECRET",
        "redirect_uri": "GOOGLE_REDIRECT_URI",
    },
    "oauth_wechat": {
        "app_id": "WECHAT_APP_ID",
        "app_secret": "WECHAT_APP_SECRET",
        "redirect_uri": "WECHAT_REDIRECT_URI",
    },
    "oauth_microsoft": {
        "client_id": "MICROSOFT_CLIENT_ID",
        "client_secret": "MICROSOFT_CLIENT_SECRET",
        "redirect_uri": "MICROSOFT_REDIRECT_URI",
    },
    "oauth_dingtalk": {
        "app_id": "DINGTALK_APP_ID",
        "app_secret": "DINGTALK_APP_SECRET",
        "redirect_uri": "DINGTALK_REDIRECT_URI",
    },
    "oauth_feishu": {
        "app_id": "FEISHU_APP_ID",
        "app_secret": "FEISHU_APP_SECRET",
        "redirect_uri": "FEISHU_REDIRECT_URI",
    },
    "oauth_wecom": {
        "corp_id": "WECOM_CORP_ID",
        "agent_id": "WECOM_AGENT_ID",
        "app_secret": "WECOM_APP_SECRET",
        "redirect_uri": "WECOM_REDIRECT_URI",
    },
    # ===== 消息通知配置 =====
    "notify_email": {
        "smtp_host": "SMTP_HOST",
        "smtp_port": "SMTP_PORT",
        "smtp_user": "SMTP_USER",
        "smtp_password": "SMTP_PASSWORD",
        "smtp_use_tls": "SMTP_USE_TLS",
        "smtp_from_name": "SMTP_FROM_NAME",
        "smtp_from_email": "SMTP_FROM_EMAIL",
    },
    "notify_dingtalk": {
        "webhook_url": "DINGTALK_WEBHOOK_URL",
        "webhook_secret": "DINGTALK_WEBHOOK_SECRET",
        "agent_id": "DINGTALK_AGENT_ID",
        "corp_id": "DINGTALK_CORP_ID",
    },
    "notify_feishu": {
        "webhook_url": "FEISHU_WEBHOOK_URL",
        "webhook_secret": "FEISHU_WEBHOOK_SECRET",
    },
    "notify_wecom": {
        "webhook_url": "WECOM_WEBHOOK_URL",
    },
    "notify_wechat_mp": {
        "template_id": "WECHAT_MP_TEMPLATE_ID",
        "url": "WECHAT_MP_URL",
        "mini_appid": "WECHAT_MP_MINI_APPID",
        "mini_page": "WECHAT_MP_MINI_PAGE",
    },
    # ===== 钉钉组织架构同步配置 =====
    "sync_dingtalk": {
        "corp_id": "DINGTALK_CORP_ID",
        "app_key": "DINGTALK_APP_KEY",
        "app_secret": "DINGTALK_APP_SECRET",
        "sync_dept_id": "",
        "sync_root_dept_id": "",
        "enable_dept_event": "",
        "enable_user_event": "",
        "callback_token": "",
        "callback_aes_key": "",
        "callback_url": "",
    },
    # ===== 企业微信组织架构同步配置 =====
    "sync_wecom": {
        "corp_id": "WECOM_SYNC_CORP_ID",
        "corp_secret": "WECOM_SYNC_CORP_SECRET",
        "sync_dept_id": "",
        "sync_root_dept_id": "",
        "enable_dept_event": "",
        "enable_user_event": "",
        "callback_token": "",
        "callback_aes_key": "",
        "callback_url": "",
    },
    # ===== 飞书组织架构同步配置 =====
    "sync_feishu": {
        "app_id": "FEISHU_SYNC_APP_ID",
        "app_secret": "FEISHU_SYNC_APP_SECRET",
        "sync_dept_id": "",
        "sync_root_dept_id": "",
        "enable_dept_event": "",
        "enable_user_event": "",
        "encrypt_key": "",
        "verification_token": "",
        "callback_url": "",
    },
    "notify_sms": {
        "provider": "SMS_PROVIDER",
        "aliyun_access_key_id": "ALIYUN_SMS_ACCESS_KEY_ID",
        "aliyun_access_key_secret": "ALIYUN_SMS_ACCESS_KEY_SECRET",
        "aliyun_sign_name": "ALIYUN_SMS_SIGN_NAME",
        "aliyun_template_code": "ALIYUN_SMS_TEMPLATE_CODE",
        "tencent_secret_id": "TENCENT_SMS_SECRET_ID",
        "tencent_secret_key": "TENCENT_SMS_SECRET_KEY",
        "tencent_sdk_app_id": "TENCENT_SMS_SDK_APP_ID",
        "tencent_sign_name": "TENCENT_SMS_SIGN_NAME",
        "tencent_template_id": "TENCENT_SMS_TEMPLATE_ID",
    },
}

# 敏感字段列表（API 返回时脱敏）
SECRET_KEYS = {
    "client_secret", "app_secret", "app_key", "corp_secret",
    "smtp_password", "webhook_secret",
    "aliyun_access_key_secret", "tencent_secret_key",
    "callback_token", "callback_aes_key",
    "encrypt_key", "verification_token",
}


class ConfigManager:
    """
    三级配置管理器

    获取优先级: Redis → 数据库 → env 配置文件
    写入: 同时写入数据库 + Redis
    """

    def __init__(self):
        self._cache = CacheManager(prefix="sys_config:")

    # ========== 读取 ==========

    async def get(self, group: str, key: str) -> Optional[str]:
        """
        获取单个配置值

        :param group: 配置分组
        :param key: 配置键
        :return: 配置值，三级都没有返回 None
        """
        # 1. Redis
        cache_key = f"{group}:{key}"
        value = await self._cache.get(cache_key)
        if value is not None:
            return value

        # 2. 数据库
        value = await self._get_from_db(group, key)
        if value is not None:
            await self._cache.set(cache_key, value, expire=CONFIG_CACHE_EXPIRE)
            return value

        # 3. env 配置文件
        value = self._get_from_env(group, key)
        if value is not None:
            # 回写到 Redis 缓存
            await self._cache.set(cache_key, value, expire=CONFIG_CACHE_EXPIRE)
        return value

    async def get_group(self, group: str) -> Dict[str, Any]:
        """
        获取整个分组的配置

        :param group: 配置分组
        :return: {key: value} 字典
        """
        # 先尝试从 Redis 获取整个分组
        group_cache_key = f"_group_:{group}"
        cached = await self._cache.get(group_cache_key)
        if cached is not None and isinstance(cached, dict):
            return cached

        # 从数据库获取该分组所有配置
        db_configs = await self._get_group_from_db(group)

        # 获取该分组的 env 映射
        env_mapping = GROUP_ENV_MAPPING.get(group, {})

        # 合并: 数据库值优先，缺失的用 env 补充
        result = {}
        for key in env_mapping:
            if key in db_configs and db_configs[key] is not None and db_configs[key] != "":
                result[key] = db_configs[key]
            else:
                env_value = self._get_from_env(group, key)
                result[key] = env_value

        # 数据库中可能有 env_mapping 之外的自定义 key
        for key, value in db_configs.items():
            if key not in result:
                result[key] = value

        # 缓存整个分组
        await self._cache.set(group_cache_key, result, expire=CONFIG_CACHE_EXPIRE)

        return result

    async def get_all_groups(self) -> Dict[str, Dict[str, Any]]:
        """获取所有分组的配置"""
        result = {}
        for group in GROUP_ENV_MAPPING:
            result[group] = await self.get_group(group)
        return result

    # ========== 写入 ==========

    async def set(self, group: str, key: str, value: Optional[str], db_session=None) -> None:
        """
        设置单个配置值（写入数据库 + 更新 Redis）

        :param group: 配置分组
        :param key: 配置键
        :param value: 配置值
        :param db_session: 数据库会话（可选，不传则自动创建）
        """
        await self._set_to_db(group, key, value, db_session)

        # 更新 Redis 单个 key 缓存
        cache_key = f"{group}:{key}"
        if value is not None:
            await self._cache.set(cache_key, value, expire=CONFIG_CACHE_EXPIRE)
        else:
            await self._cache.delete(cache_key)

        # 清除分组缓存（下次 get_group 会重新加载）
        await self._invalidate_group_cache(group)

    async def set_group(self, group: str, configs: Dict[str, Optional[str]], db_session=None) -> None:
        """
        批量设置分组配置

        :param group: 配置分组
        :param configs: {key: value} 字典
        :param db_session: 数据库会话
        """
        for key, value in configs.items():
            await self._set_to_db(group, key, value, db_session)

            cache_key = f"{group}:{key}"
            if value is not None:
                await self._cache.set(cache_key, value, expire=CONFIG_CACHE_EXPIRE)
            else:
                await self._cache.delete(cache_key)

        # 清除分组缓存
        await self._invalidate_group_cache(group)

    # ========== 缓存管理 ==========

    async def invalidate(self, group: str, key: str) -> None:
        """清除单个配置的缓存"""
        await self._cache.delete(f"{group}:{key}")
        await self._invalidate_group_cache(group)

    async def invalidate_group(self, group: str) -> None:
        """清除整个分组的缓存"""
        env_mapping = GROUP_ENV_MAPPING.get(group, {})
        for key in env_mapping:
            await self._cache.delete(f"{group}:{key}")
        await self._invalidate_group_cache(group)

    async def invalidate_all(self) -> None:
        """清除所有配置缓存"""
        await self._cache.delete_pattern("*")

    async def warmup(self) -> None:
        """
        预热: 启动时将数据库配置加载到 Redis
        """
        logger.info("开始预热系统配置到 Redis...")
        try:
            for group in GROUP_ENV_MAPPING:
                await self.get_group(group)
            logger.info("系统配置预热完成")
        except Exception as e:
            logger.warning(f"系统配置预热失败（将使用 env 配置文件兜底）: {e}")

    # ========== 内部方法 ==========

    async def _invalidate_group_cache(self, group: str) -> None:
        """清除分组级缓存"""
        await self._cache.delete(f"_group_:{group}")

    async def _get_from_db(self, group: str, key: str) -> Optional[str]:
        """从数据库获取配置"""
        try:
            from app.database import AsyncSessionLocal
            from core.system_config.model import SystemConfig
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SystemConfig.config_value).where(
                        SystemConfig.config_group == group,
                        SystemConfig.config_key == key,
                        SystemConfig.status == True,  # noqa: E712
                        SystemConfig.is_deleted == False,  # noqa: E712
                    )
                )
                row = result.scalar_one_or_none()
                return row
        except Exception as e:
            logger.debug(f"从数据库获取配置失败 {group}.{key}: {e}")
            return None

    async def _get_group_from_db(self, group: str) -> Dict[str, str]:
        """从数据库获取整个分组"""
        try:
            from app.database import AsyncSessionLocal
            from core.system_config.model import SystemConfig
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SystemConfig.config_key, SystemConfig.config_value).where(
                        SystemConfig.config_group == group,
                        SystemConfig.status == True,  # noqa: E712
                        SystemConfig.is_deleted == False,  # noqa: E712
                    )
                )
                return {row[0]: row[1] for row in result.all()}
        except Exception as e:
            logger.debug(f"从数据库获取分组配置失败 {group}: {e}")
            return {}

    async def _set_to_db(self, group: str, key: str, value: Optional[str], db_session=None) -> None:
        """写入数据库（upsert）"""
        from core.system_config.model import SystemConfig
        from sqlalchemy import select

        async def _do_upsert(db):
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

        if db_session:
            await _do_upsert(db_session)
        else:
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await _do_upsert(db)

    def _get_from_env(self, group: str, key: str) -> Optional[str]:
        """从 env 配置文件获取"""
        from app.config import settings

        env_mapping = GROUP_ENV_MAPPING.get(group, {})
        attr_name = env_mapping.get(key)
        if not attr_name:
            return None

        value = getattr(settings, attr_name, None)
        if value is None:
            return None
        return str(value)

    # ========== 工具方法 ==========

    @staticmethod
    def mask_value(value: Optional[str]) -> Optional[str]:
        """脱敏处理"""
        if not value:
            return value
        if len(value) <= 6:
            return "***"
        return value[:3] + "***" + value[-3:]

    @staticmethod
    def get_group_list() -> List[Dict[str, str]]:
        """获取所有配置分组定义"""
        groups = []
        for group_key in GROUP_ENV_MAPPING:
            groups.append({
                "key": group_key,
                "fields": list(GROUP_ENV_MAPPING[group_key].keys()),
            })
        return groups

    @staticmethod
    def is_secret_key(key: str) -> bool:
        """判断是否为敏感字段"""
        return key in SECRET_KEYS


# 全局单例
config_manager = ConfigManager()
