"""
微信公众号模板消息工具

通过微信服务号向关注用户发送模板消息。
前提条件：
1. 需要微信认证服务号（订阅号无模板消息权限）
2. 用户需关注该公众号，系统记录用户的 openid
3. 在公众号后台添加消息模板，获取 template_id
4. 复用 WECHAT_APP_ID / WECHAT_APP_SECRET（与 OAuth 登录同一应用）
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WechatMPMessage:
    """微信公众号模板消息"""

    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"

    _access_token: Optional[str] = None
    _token_expires_at: float = 0

    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置（仅检查 env，同步兼容）"""
        return bool(
            settings.WECHAT_APP_ID
            and settings.WECHAT_APP_SECRET
            and settings.WECHAT_MP_TEMPLATE_ID
        )

    @classmethod
    async def is_configured_async(cls) -> bool:
        """检查是否已配置（通过 config_manager 三级获取）"""
        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wechat")
        mp_config = await config_manager.get_group("notify_wechat_mp")
        return bool(
            oauth_config.get("app_id")
            and oauth_config.get("app_secret")
            and mp_config.get("template_id")
        )

    @classmethod
    async def _get_access_token(cls) -> Optional[str]:
        """获取 access_token（带缓存）"""
        now = time.time()
        if cls._access_token and now < cls._token_expires_at:
            return cls._access_token

        from app.config_manager import config_manager
        oauth_config = await config_manager.get_group("oauth_wechat")
        app_id = oauth_config.get("app_id")
        app_secret = oauth_config.get("app_secret")
        if not (app_id and app_secret):
            logger.warning("微信 app_id/app_secret 未配置")
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    cls.TOKEN_URL,
                    params={
                        "grant_type": "client_credential",
                        "appid": app_id,
                        "secret": app_secret,
                    },
                )
                resp.raise_for_status()
                result = resp.json()

                if "access_token" in result:
                    cls._access_token = result["access_token"]
                    cls._token_expires_at = now + result.get("expires_in", 7200) - 300
                    logger.info("微信公众号 access_token 获取成功")
                    return cls._access_token
                else:
                    logger.error(f"获取微信公众号 access_token 失败: {result}")
                    return None
        except Exception as e:
            logger.error(f"获取微信公众号 access_token 异常: {e}")
            return None

    @classmethod
    async def send_template(
            cls,
            openid: str,
            template_data: Dict[str, Dict[str, str]],
            template_id: str = None,
            url: str = None,
            miniprogram: Dict[str, str] = None,
    ) -> bool:
        """
        发送模板消息

        Args:
            openid: 用户的 openid
            template_data: 模板数据，格式如:
                {
                    "first": {"value": "通知标题", "color": "#173177"},
                    "keyword1": {"value": "内容1"},
                    "keyword2": {"value": "内容2"},
                    "remark": {"value": "备注信息"}
                }
            template_id: 模板ID，默认使用配置的 WECHAT_MP_TEMPLATE_ID
            url: 点击跳转链接，默认使用配置的 WECHAT_MP_URL
            miniprogram: 跳转小程序配置 {"appid": "...", "pagepath": "..."}
        """
        if not await cls.is_configured_async():
            logger.warning("微信公众号模板消息未配置，跳过发送")
            return False

        token = await cls._get_access_token()
        if not token:
            return False

        from app.config_manager import config_manager
        mp_config = await config_manager.get_group("notify_wechat_mp")

        try:
            payload: Dict[str, Any] = {
                "touser": openid,
                "template_id": template_id or mp_config.get("template_id") or settings.WECHAT_MP_TEMPLATE_ID,
                "data": template_data,
            }

            # 跳转链接
            jump_url = url or mp_config.get("url") or settings.WECHAT_MP_URL
            if jump_url:
                payload["url"] = jump_url

            # 小程序跳转（优先级高于 url）
            mini = miniprogram
            mini_appid = mp_config.get("mini_appid") or settings.WECHAT_MP_MINI_APPID
            if not mini and mini_appid:
                mini = {
                    "appid": mini_appid,
                    "pagepath": mp_config.get("mini_page") or settings.WECHAT_MP_MINI_PAGE or "",
                }
            if mini:
                payload["miniprogram"] = mini

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{cls.SEND_URL}?access_token={token}",
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()

                if result.get("errcode") == 0:
                    logger.info(f"微信模板消息发送成功: {openid}")
                    return True
                else:
                    logger.error(f"微信模板消息发送失败: {result}")
                    return False
        except Exception as e:
            logger.error(f"微信模板消息请求异常: {e}")
            return False

    @classmethod
    async def send_notification(
            cls,
            openid: str,
            title: str,
            content: str,
            remark: str = "",
            url: str = None,
    ) -> bool:
        """
        发送通知类模板消息（简化接口）

        使用通用模板格式:
            first: 标题
            keyword1: 通知内容
            keyword2: 时间
            remark: 备注

        Args:
            openid: 用户的 openid
            title: 通知标题
            content: 通知内容
            remark: 备注信息
            url: 点击跳转链接
        """
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app_name = settings.APP_NAME

        template_data = {
            "first": {"value": title, "color": "#173177"},
            "keyword1": {"value": content},
            "keyword2": {"value": now_str},
            "remark": {"value": remark or f"来自 {app_name}"},
        }
        return await cls.send_template(openid, template_data, url=url)

    @classmethod
    async def batch_send_notification(
            cls,
            openids: List[str],
            title: str,
            content: str,
            remark: str = "",
            url: str = None,
    ) -> int:
        """
        批量发送通知类模板消息

        Args:
            openids: 用户 openid 列表
            title: 通知标题
            content: 通知内容
            remark: 备注信息
            url: 点击跳转链接

        Returns:
            成功发送的数量
        """
        success_count = 0
        for openid in openids:
            try:
                ok = await cls.send_notification(openid, title, content, remark, url)
                if ok:
                    success_count += 1
            except Exception as e:
                logger.warning(f"微信模板消息发送失败 [{openid}]: {e}")
        return success_count
