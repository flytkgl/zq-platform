"""
飞书通知工具

支持两种通知方式：
1. Webhook 群机器人 - 向飞书群聊发送消息
2. 应用消息 - 通过企业自建应用向个人发送消息
"""
import base64
import hashlib
import hmac
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class FeishuWebhook:
    """飞书群机器人 Webhook"""

    @staticmethod
    async def _get_config() -> dict:
        """通过 config_manager 三级获取飞书 Webhook 配置"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_feishu")
        return {
            "webhook_url": group_config.get("webhook_url") or None,
            "webhook_secret": group_config.get("webhook_secret") or None,
        }

    @staticmethod
    def is_configured() -> bool:
        """检查 Webhook 是否已配置（仅检查 env，同步兼容）"""
        return bool(settings.FEISHU_WEBHOOK_URL)

    @staticmethod
    async def is_configured_async() -> bool:
        """检查 Webhook 是否已配置（通过 config_manager 三级获取）"""
        config = await FeishuWebhook._get_config()
        return bool(config["webhook_url"])

    @staticmethod
    def _sign(timestamp: str, secret: str = None) -> str:
        """生成签名"""
        if not secret:
            return ""

        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    @staticmethod
    async def send_text(text: str) -> bool:
        """
        发送文本消息

        Args:
            text: 消息内容
        """
        config = await FeishuWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("飞书 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msg_type": "text",
            "content": {"text": text},
        }
        return await FeishuWebhook._post(payload, config)

    @staticmethod
    async def send_rich_text(title: str, content_lines: List[List[Dict[str, Any]]]) -> bool:
        """
        发送富文本消息

        Args:
            title: 消息标题
            content_lines: 富文本内容行列表，每行是一个元素列表
                例: [[{"tag": "text", "text": "内容"}]]
        """
        config = await FeishuWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("飞书 Webhook 未配置，跳过发送")
            return False

        payload: Dict[str, Any] = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content_lines,
                    }
                }
            },
        }
        return await FeishuWebhook._post(payload, config)

    @staticmethod
    async def send_interactive(title: str, content: str, button_text: str = "", button_url: str = "") -> bool:
        """
        发送交互式卡片消息

        Args:
            title: 卡片标题
            content: 卡片内容（Markdown 格式）
            button_text: 按钮文字
            button_url: 按钮链接
        """
        config = await FeishuWebhook._get_config()
        if not config["webhook_url"]:
            logger.warning("飞书 Webhook 未配置，跳过发送")
            return False

        elements = [
            {
                "tag": "div",
                "text": {
                    "content": content,
                    "tag": "lark_md",
                },
            }
        ]

        if button_text and button_url:
            elements.append({
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"content": button_text, "tag": "plain_text"},
                        "url": button_url,
                        "type": "primary",
                    }
                ],
            })

        payload: Dict[str, Any] = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"content": title, "tag": "plain_text"},
                    "template": "blue",
                },
                "elements": elements,
            },
        }
        return await FeishuWebhook._post(payload, config)

    @staticmethod
    async def _post(payload: Dict[str, Any], config: dict = None) -> bool:
        """发送请求到飞书 Webhook"""
        try:
            if config is None:
                config = await FeishuWebhook._get_config()
            url = config["webhook_url"]

            # 添加签名
            webhook_secret = config.get("webhook_secret") or ""
            if webhook_secret:
                timestamp = str(int(time.time()))
                sign = FeishuWebhook._sign(timestamp, webhook_secret)
                payload["timestamp"] = timestamp
                payload["sign"] = sign

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                result = resp.json()

                if result.get("code") == 0 or result.get("StatusCode") == 0:
                    logger.info("飞书 Webhook 消息发送成功")
                    return True
                else:
                    logger.error(f"飞书 Webhook 发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"飞书 Webhook 请求异常: {e}")
            return False


class FeishuAppMessage:
    """飞书应用消息（企业自建应用）"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
    BATCH_SEND_URL = "https://open.feishu.cn/open-apis/message/v4/batch_send/"
    USER_ID_URL = "https://open.feishu.cn/open-apis/contact/v3/users/batch"

    _tenant_access_token: Optional[str] = None
    _token_expires_at: float = 0

    @classmethod
    def is_configured(cls) -> bool:
        """检查应用消息是否已配置（仅检查 env，同步兼容）"""
        return bool(settings.FEISHU_APP_ID and settings.FEISHU_APP_SECRET)

    @classmethod
    async def is_configured_async(cls) -> bool:
        """检查应用消息是否已配置（通过 config_manager 三级获取）"""
        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_feishu")
        return bool(oauth_config.get("app_id") and oauth_config.get("app_secret"))

    @classmethod
    async def _get_tenant_access_token(cls) -> Optional[str]:
        """获取 tenant_access_token（带缓存）"""
        now = time.time()
        if cls._tenant_access_token and now < cls._token_expires_at:
            return cls._tenant_access_token

        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_feishu")
        app_id = oauth_config.get("app_id")
        app_secret = oauth_config.get("app_secret")
        if not (app_id and app_secret):
            logger.warning("飞书 app_id/app_secret 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    cls.TOKEN_URL,
                    json={
                        "app_id": app_id,
                        "app_secret": app_secret,
                    },
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("code") == 0:
                    cls._tenant_access_token = result["tenant_access_token"]
                    cls._token_expires_at = now + result.get("expire", 7200) - 300
                    logger.info("飞书 tenant_access_token 获取成功")
                    return cls._tenant_access_token
                else:
                    logger.error(f"获取飞书 tenant_access_token 失败: {result}")
                    return None
        except Exception as e:
            logger.error(f"获取飞书 tenant_access_token 异常: {e}")
            return None

    @classmethod
    async def send_text(cls, open_id: str, text: str) -> bool:
        """
        发送文本消息给个人

        Args:
            open_id: 飞书用户 open_id
            text: 消息内容
        """
        content = {"text": text}
        return await cls._send(open_id, "text", content)

    @classmethod
    async def send_interactive(cls, open_id: str, title: str, content_text: str) -> bool:
        """
        发送交互式卡片消息给个人

        Args:
            open_id: 飞书用户 open_id
            title: 卡片标题
            content_text: 卡片内容（Markdown）
        """
        card = {
            "header": {
                "title": {"content": title, "tag": "plain_text"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"content": content_text, "tag": "lark_md"},
                }
            ],
        }
        return await cls._send(open_id, "interactive", card)

    @classmethod
    async def send_batch_text(cls, open_ids: List[str], text: str) -> bool:
        """
        批量发送文本消息

        Args:
            open_ids: 飞书用户 open_id 列表
            text: 消息内容
        """
        if not await cls.is_configured_async():
            logger.warning("飞书应用消息未配置，跳过发送")
            return False

        token = await cls._get_tenant_access_token()
        if not token:
            return False

        try:
            payload = {
                "open_ids": open_ids,
                "msg_type": "text",
                "content": {"text": text},
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    cls.BATCH_SEND_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("code") == 0:
                    logger.info(f"飞书批量消息发送成功: {len(open_ids)} 人")
                    return True
                else:
                    logger.error(f"飞书批量消息发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"飞书批量消息请求异常: {e}")
            return False

    @classmethod
    async def _send(cls, open_id: str, msg_type: str, content: Dict[str, Any]) -> bool:
        """发送消息给个人"""
        if not await cls.is_configured_async():
            logger.warning("飞书应用消息未配置，跳过发送")
            return False

        token = await cls._get_tenant_access_token()
        if not token:
            return False

        try:
            import json
            payload = {
                "receive_id": open_id,
                "msg_type": msg_type,
                "content": json.dumps(content) if msg_type != "interactive" else json.dumps(content),
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{cls.SEND_URL}?receive_id_type=open_id",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("code") == 0:
                    logger.info(f"飞书消息发送成功: {open_id}")
                    return True
                else:
                    logger.error(f"飞书消息发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"飞书消息请求异常: {e}")
            return False

    @classmethod
    async def get_open_ids_by_union_ids(cls, union_ids: List[str]) -> Dict[str, str]:
        """
        通过 union_id 批量获取 open_id

        Args:
            union_ids: 飞书 union_id 列表

        Returns:
            {union_id: open_id} 映射
        """
        if not await cls.is_configured_async():
            return {}

        token = await cls._get_tenant_access_token()
        if not token:
            return {}

        result_map = {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 飞书批量查询接口每次最多50个
                for i in range(0, len(union_ids), 50):
                    batch = union_ids[i:i + 50]
                    params = [("user_ids", uid) for uid in batch]
                    params.append(("user_id_type", "union_id"))

                    resp = await client.get(
                        cls.USER_ID_URL,
                        headers={"Authorization": f"Bearer {token}"},
                        params=params,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("code") == 0:
                        items = data.get("data", {}).get("items", [])
                        for item in items:
                            union_id = item.get("union_id", "")
                            open_id = item.get("open_id", "")
                            if union_id and open_id:
                                result_map[union_id] = open_id
                    else:
                        logger.warning(f"飞书批量查询用户失败: {data}")
        except Exception as e:
            logger.error(f"飞书批量查询用户异常: {e}")

        return result_map


def build_feishu_notification_text(title: str, content: str, app_name: str = None) -> str:
    """构建飞书通知的文本内容"""
    app = app_name or settings.APP_NAME
    return f"【{app}】{title}\n{content}"
