"""
企业微信通知工具

支持两种通知方式：
1. Webhook 群机器人 - 向企业微信群聊发送消息
2. 应用消息 - 通过企业自建应用向个人发送消息（复用 OAuth 配置）
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WecomWebhook:
    """企业微信群机器人 Webhook"""

    @staticmethod
    async def _get_config() -> dict:
        """通过 config_manager 三级获取企业微信 Webhook 配置"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_wecom")
        return {
            "webhook_url": group_config.get("webhook_url") or None,
        }

    @staticmethod
    def is_configured() -> bool:
        """检查 Webhook 是否已配置（仅检查 env，同步兼容）"""
        return bool(settings.WECOM_WEBHOOK_URL)

    @staticmethod
    async def is_configured_async() -> bool:
        """检查 Webhook 是否已配置（通过 config_manager 三级获取）"""
        config = await WecomWebhook._get_config()
        return bool(config["webhook_url"])

    @staticmethod
    async def send_text(content: str, mentioned_list: List[str] = None, mentioned_mobile_list: List[str] = None) -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容（最长2048字节）
            mentioned_list: @指定用户的 userid 列表，@all 表示所有人
            mentioned_mobile_list: @指定手机号列表
        """
        config = await WecomWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("企业微信 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or [],
                "mentioned_mobile_list": mentioned_mobile_list or [],
            },
        }
        return await WecomWebhook._post(payload, config)

    @staticmethod
    async def send_markdown(content: str) -> bool:
        """
        发送 Markdown 消息

        Args:
            content: Markdown 格式内容（最长4096字节）
                支持语法: 标题(#)、加粗(**)、链接、引用(>)、字体颜色(<font>)
        """
        config = await WecomWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("企业微信 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msgtype": "markdown",
            "markdown": {"content": content},
        }
        return await WecomWebhook._post(payload, config)

    @staticmethod
    async def send_news(title: str, description: str = "", url: str = "", picurl: str = "") -> bool:
        """
        发送图文消息

        Args:
            title: 标题（不超过128字节）
            description: 描述（不超过512字节）
            url: 点击跳转链接
            picurl: 图片链接
        """
        config = await WecomWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("企业微信 Webhook 未配置，跳过发送")
            return False

        article: Dict[str, Any] = {"title": title}
        if description:
            article["description"] = description
        if url:
            article["url"] = url
        if picurl:
            article["picurl"] = picurl

        payload: Dict[str, Any] = {
            "msgtype": "news",
            "news": {"articles": [article]},
        }
        return await WecomWebhook._post(payload, config)

    @staticmethod
    async def _post(payload: Dict[str, Any], config: dict = None) -> bool:
        """发送请求到企业微信 Webhook"""
        try:
            if config is None:
                config = await WecomWebhook._get_config()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(config["webhook_url"], json=payload)
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    logger.info("企业微信 Webhook 消息发送成功")
                    return True
                else:
                    logger.error(f"企业微信 Webhook 发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"企业微信 Webhook 请求异常: {e}")
            return False


class WecomAppMessage:
    """企业微信应用消息（企业自建应用，复用 OAuth 配置）"""

    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    SEND_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"

    _access_token: Optional[str] = None
    _token_expires_at: float = 0

    @classmethod
    def is_configured(cls) -> bool:
        """检查应用消息是否已配置（仅检查 env，同步兼容）"""
        return bool(
            settings.WECOM_CORP_ID
            and settings.WECOM_APP_SECRET
            and settings.WECOM_AGENT_ID
        )

    @classmethod
    async def is_configured_async(cls) -> bool:
        """检查应用消息是否已配置（通过 config_manager 三级获取）"""
        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wecom")
        return bool(
            oauth_config.get("corp_id")
            and oauth_config.get("app_secret")
            and oauth_config.get("agent_id")
        )

    @classmethod
    async def _get_access_token(cls) -> Optional[str]:
        """获取 access_token（带缓存）"""
        now = time.time()
        if cls._access_token and now < cls._token_expires_at:
            return cls._access_token

        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wecom")
        corp_id = oauth_config.get("corp_id")
        app_secret = oauth_config.get("app_secret")
        if not (corp_id and app_secret):
            logger.warning("企业微信 corp_id/app_secret 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cls.TOKEN_URL,
                    params={
                        "corpid": corp_id,
                        "corpsecret": app_secret,
                    },
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    cls._access_token = result["access_token"]
                    cls._token_expires_at = now + result.get("expires_in", 7200) - 300
                    logger.info("企业微信 access_token 获取成功")
                    return cls._access_token
                else:
                    logger.error(f"获取企业微信 access_token 失败: {result}")
                    return None
        except Exception as e:
            logger.error(f"获取企业微信 access_token 异常: {e}")
            return None

    @classmethod
    async def send_text(cls, userid_list: List[str], content: str) -> bool:
        """
        发送文本消息给个人

        Args:
            userid_list: 企业微信 userid 列表（最多1000个，用|分隔）
            content: 消息内容
        """
        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wecom")
        agent_id = oauth_config.get("agent_id") or settings.WECOM_AGENT_ID
        msg = {
            "touser": "|".join(userid_list[:1000]),
            "msgtype": "text",
            "agentid": int(agent_id),
            "text": {"content": content},
        }
        return await cls._send(msg)

    @classmethod
    async def send_textcard(
            cls,
            userid_list: List[str],
            title: str,
            description: str,
            url: str = "",
            btntxt: str = "详情",
    ) -> bool:
        """
        发送文本卡片消息给个人

        Args:
            userid_list: 企业微信 userid 列表
            title: 标题（不超过128字节）
            description: 描述（支持<div>标签）
            url: 点击跳转链接
            btntxt: 按钮文字
        """
        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wecom")
        agent_id = oauth_config.get("agent_id") or settings.WECOM_AGENT_ID
        msg = {
            "touser": "|".join(userid_list[:1000]),
            "msgtype": "textcard",
            "agentid": int(agent_id),
            "textcard": {
                "title": title,
                "description": description,
                "url": url or "URL",
                "btntxt": btntxt,
            },
        }
        return await cls._send(msg)

    @classmethod
    async def send_markdown(cls, userid_list: List[str], content: str) -> bool:
        """
        发送 Markdown 消息给个人

        Args:
            userid_list: 企业微信 userid 列表
            content: Markdown 格式内容
        """
        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wecom")
        agent_id = oauth_config.get("agent_id") or settings.WECOM_AGENT_ID
        msg = {
            "touser": "|".join(userid_list[:1000]),
            "msgtype": "markdown",
            "agentid": int(agent_id),
            "markdown": {"content": content},
        }
        return await cls._send(msg)

    @classmethod
    async def _send(cls, msg: Dict[str, Any]) -> bool:
        """发送应用消息"""
        if not await cls.is_configured_async():
            logger.warning("企业微信应用消息未配置，跳过发送")
            return False

        token = await cls._get_access_token()
        if not token:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    cls.SEND_URL,
                    params={"access_token": token},
                    json=msg,
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    logger.info(f"企业微信应用消息发送成功")
                    return True
                else:
                    logger.error(f"企业微信应用消息发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"企业微信应用消息请求异常: {e}")
            return False


def build_wecom_markdown(title: str, content: str, app_name: str = None) -> str:
    """
    构建企业微信通知的 Markdown 内容

    Args:
        title: 通知标题
        content: 通知内容
        app_name: 应用名称
    """
    app = app_name or settings.APP_NAME
    return f"**{title}**\n{content}\n> 来自 {app}"
