"""
钉钉通知工具

支持两种通知方式：
1. Webhook 群机器人 - 向钉钉群聊发送消息
2. 工作通知 - 通过企业内部应用向个人发送工作通知
"""
import base64
import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class DingTalkWebhook:
    """钉钉群机器人 Webhook"""

    @staticmethod
    async def _get_config() -> dict:
        """通过 config_manager 三级获取钉钉 Webhook 配置"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_dingtalk")
        return {
            "webhook_url": group_config.get("webhook_url") or None,
            "webhook_secret": group_config.get("webhook_secret") or None,
        }

    @staticmethod
    def is_configured() -> bool:
        """检查 Webhook 是否已配置（仅检查 env，同步兼容）"""
        return bool(settings.DINGTALK_WEBHOOK_URL)

    @staticmethod
    async def is_configured_async() -> bool:
        """检查 Webhook 是否已配置（通过 config_manager 三级获取）"""
        config = await DingTalkWebhook._get_config()
        return bool(config["webhook_url"])

    @staticmethod
    def _sign_with_secret(secret: str) -> Dict[str, str]:
        """使用指定 secret 生成签名参数"""
        if not secret:
            return {}

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return {"timestamp": timestamp, "sign": sign}

    @staticmethod
    async def send_text(content: str, at_mobiles: List[str] = None, at_all: bool = False) -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容
            at_mobiles: @指定手机号列表
            at_all: 是否@所有人
        """
        config = await DingTalkWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("钉钉 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msgtype": "text",
            "text": {"content": content},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all,
            },
        }
        return await DingTalkWebhook._post(payload, config)

    @staticmethod
    async def send_markdown(title: str, text: str, at_mobiles: List[str] = None, at_all: bool = False) -> bool:
        """
        发送 Markdown 消息

        Args:
            title: 消息标题（会话列表中展示）
            text: Markdown 格式内容
            at_mobiles: @指定手机号列表
            at_all: 是否@所有人
        """
        config = await DingTalkWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("钉钉 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all,
            },
        }
        return await DingTalkWebhook._post(payload, config)

    @staticmethod
    async def send_action_card(title: str, text: str, single_url: str = "", single_title: str = "查看详情") -> bool:
        """
        发送 ActionCard 消息

        Args:
            title: 消息标题
            text: Markdown 格式内容
            single_url: 跳转链接
            single_title: 按钮文字
        """
        config = await DingTalkWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("钉钉 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "singleTitle": single_title,
                "singleURL": single_url,
            },
        }
        return await DingTalkWebhook._post(payload, config)

    @staticmethod
    async def _post(payload: Dict[str, Any], config: dict = None) -> bool:
        """发送请求到钉钉 Webhook"""
        try:
            if config is None:
                config = await DingTalkWebhook._get_config()
            url = config["webhook_url"]
            sign_params = DingTalkWebhook._sign_with_secret(config.get("webhook_secret") or "")
            if sign_params:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}timestamp={sign_params['timestamp']}&sign={sign_params['sign']}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    logger.info("钉钉 Webhook 消息发送成功")
                    return True
                else:
                    logger.error(f"钉钉 Webhook 发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"钉钉 Webhook 请求异常: {e}")
            return False


class DingTalkWorkNotice:
    """钉钉工作通知（企业内部应用）"""

    TOKEN_URL = "https://oapi.dingtalk.com/gettoken"
    SEND_URL = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"

    _access_token: Optional[str] = None
    _token_expires_at: float = 0

    @classmethod
    async def _get_config(cls) -> dict:
        """通过 config_manager 三级获取钉钉工作通知配置"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_dingtalk")
        return {
            "agent_id": group_config.get("agent_id") or None,
            "corp_id": group_config.get("corp_id") or None,
            "app_id": group_config.get("webhook_url") and None,  # webhook_url 不用于工作通知
        }

    @classmethod
    def is_configured(cls) -> bool:
        """检查工作通知是否已配置（仅检查 env，同步兼容）"""
        return bool(
            settings.DINGTALK_APP_ID
            and settings.DINGTALK_APP_SECRET
            and settings.DINGTALK_AGENT_ID
        )

    @classmethod
    async def is_configured_async(cls) -> bool:
        """检查工作通知是否已配置（通过 config_manager 三级获取）"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_dingtalk")
        # 工作通知需要 agent_id + OAuth 配置中的 app_id/app_secret
        agent_id = group_config.get("agent_id") or None
        # app_id/app_secret 来自 oauth_dingtalk 分组
        oauth_config = await config_manager.get_group("oauth_dingtalk")
        app_id = oauth_config.get("app_id") or None
        app_secret = oauth_config.get("app_secret") or None
        return bool(app_id and app_secret and agent_id)

    @classmethod
    async def _get_access_token(cls) -> Optional[str]:
        """获取企业内部应用的 access_token（带缓存）"""
        now = time.time()
        if cls._access_token and now < cls._token_expires_at:
            return cls._access_token

        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_dingtalk")
        app_id = oauth_config.get("app_id")
        app_secret = oauth_config.get("app_secret")
        if not (app_id and app_secret):
            logger.warning("钉钉 app_id/app_secret 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cls.TOKEN_URL,
                    params={
                        "appkey": app_id,
                        "appsecret": app_secret,
                    },
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    cls._access_token = result["access_token"]
                    cls._token_expires_at = now + result.get("expires_in", 7200) - 300
                    logger.info("钉钉 access_token 获取成功")
                    return cls._access_token
                else:
                    logger.error(f"获取钉钉 access_token 失败: {result}")
                    return None
        except Exception as e:
            logger.error(f"获取钉钉 access_token 异常: {e}")
            return None

    @classmethod
    async def send_text(cls, userid_list: List[str], content: str) -> bool:
        """
        发送文本工作通知

        Args:
            userid_list: 钉钉用户 userId 列表（最多100个）
            content: 消息内容
        """
        return await cls._send(userid_list, {"msgtype": "text", "text": {"content": content}})

    @classmethod
    async def send_markdown(cls, userid_list: List[str], title: str, text: str) -> bool:
        """
        发送 Markdown 工作通知

        Args:
            userid_list: 钉钉用户 userId 列表
            title: 消息标题
            text: Markdown 格式内容
        """
        return await cls._send(userid_list, {"msgtype": "markdown", "markdown": {"title": title, "text": text}})

    @classmethod
    async def send_action_card(
            cls,
            userid_list: List[str],
            title: str,
            markdown: str,
            single_url: str = "",
            single_title: str = "查看详情",
    ) -> bool:
        """
        发送 ActionCard 工作通知

        Args:
            userid_list: 钉钉用户 userId 列表
            title: 消息标题
            markdown: Markdown 格式内容
            single_url: 跳转链接
            single_title: 按钮文字
        """
        return await cls._send(userid_list, {
            "msgtype": "action_card",
            "action_card": {
                "title": title,
                "markdown": markdown,
                "single_title": single_title,
                "single_url": single_url,
            },
        })

    @classmethod
    async def _send(cls, userid_list: List[str], msg: Dict[str, Any]) -> bool:
        """发送工作通知"""
        if not await cls.is_configured_async():
            logger.warning("钉钉工作通知未配置，跳过发送")
            return False

        token = await cls._get_access_token()
        if not token:
            return False

        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_dingtalk")
        agent_id = group_config.get("agent_id") or settings.DINGTALK_AGENT_ID

        try:
            payload = {
                "agent_id": agent_id,
                "userid_list": ",".join(userid_list[:100]),
                "msg": msg,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    cls.SEND_URL,
                    params={"access_token": token},
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    logger.info(f"钉钉工作通知发送成功: {len(userid_list)} 人")
                    return True
                else:
                    logger.error(f"钉钉工作通知发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"钉钉工作通知请求异常: {e}")
            return False


def build_dingtalk_markdown(title: str, content: str, app_name: str = None) -> str:
    """
    构建钉钉通知的 Markdown 内容

    Args:
        title: 通知标题
        content: 通知内容
        app_name: 应用名称
    """
    app = app_name or settings.APP_NAME
    return f"### {title}\n\n{content}\n\n---\n> 来自 {app}"
