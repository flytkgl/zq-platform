"""
异步邮件发送工具

使用 aiosmtplib 实现异步 SMTP 邮件发送，支持：
- 纯文本邮件
- HTML 邮件
- 批量发送（并发）
- 自动 TLS/SSL
"""
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


class EmailSender:
    """异步邮件发送器"""

    @staticmethod
    async def _get_smtp_config() -> dict:
        """
        通过 config_manager 三级获取 SMTP 配置（Redis → 数据库 → env）
        """
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_email")
        return {
            "host": group_config.get("smtp_host") or None,
            "port": int(group_config.get("smtp_port") or settings.SMTP_PORT or 465),
            "user": group_config.get("smtp_user") or None,
            "password": group_config.get("smtp_password") or None,
            "use_tls": str(group_config.get("smtp_use_tls", "True")).lower() in ("true", "1", "yes"),
            "from_name": group_config.get("smtp_from_name") or settings.APP_NAME,
            "from_email": group_config.get("smtp_from_email") or group_config.get("smtp_user") or None,
        }

    @staticmethod
    def is_configured() -> bool:
        """检查 SMTP 是否已配置（仅检查 env，同步兼容）"""
        return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)

    @staticmethod
    async def is_configured_async() -> bool:
        """检查 SMTP 是否已配置（通过 config_manager 三级获取）"""
        config = await EmailSender._get_smtp_config()
        return bool(config["host"] and config["user"] and config["password"])

    @staticmethod
    def _build_from_address(config: dict) -> str:
        """根据配置构建发件人地址"""
        from_email = config["from_email"] or config["user"]
        from_name = config["from_name"] or settings.APP_NAME
        return f"{from_name} <{from_email}>"

    @staticmethod
    def _get_from_address() -> str:
        """获取发件人地址（同步兼容，仅读 env）"""
        from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        from_name = settings.SMTP_FROM_NAME or settings.APP_NAME
        return f"{from_name} <{from_email}>"

    @staticmethod
    async def send(
            to_email: str,
            subject: str,
            content: str,
            html: bool = False,
    ) -> bool:
        """
        发送单封邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容（纯文本或 HTML）
            html: 是否为 HTML 内容

        Returns:
            是否发送成功
        """
        config = await EmailSender._get_smtp_config()
        if not (config["host"] and config["user"] and config["password"]):
            logger.warning("SMTP 未配置，跳过邮件发送")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = EmailSender._build_from_address(config)
            msg["To"] = to_email
            msg["Subject"] = subject

            if html:
                msg.attach(MIMEText(content, "html", "utf-8"))
            else:
                msg.attach(MIMEText(content, "plain", "utf-8"))

            # sender 必须使用 smtp_user，部分邮箱（如QQ）要求 MAIL FROM 与认证用户一致
            sender = config["user"]
            if config["use_tls"]:
                await aiosmtplib.send(
                    msg,
                    sender=sender,
                    hostname=config["host"],
                    port=config["port"],
                    username=config["user"],
                    password=config["password"],
                    use_tls=True,
                )
            else:
                await aiosmtplib.send(
                    msg,
                    sender=sender,
                    hostname=config["host"],
                    port=config["port"],
                    username=config["user"],
                    password=config["password"],
                    start_tls=True,
                )

            logger.info(f"邮件发送成功: {to_email}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败 [{to_email}]: {e}")
            return False

    @staticmethod
    async def send_batch(
            to_emails: List[str],
            subject: str,
            content: str,
            html: bool = False,
    ) -> Dict[str, bool]:
        """
        批量发送邮件（并发）

        Args:
            to_emails: 收件人邮箱列表
            subject: 邮件主题
            content: 邮件内容
            html: 是否为 HTML 内容

        Returns:
            每个邮箱的发送结果
        """
        config = await EmailSender._get_smtp_config()
        if not (config["host"] and config["user"] and config["password"]):
            logger.warning("SMTP 未配置，跳过批量邮件发送")
            return {email: False for email in to_emails}

        tasks = [
            EmailSender.send(email, subject, content, html)
            for email in to_emails
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            email: (result is True)
            for email, result in zip(to_emails, results)
        }

    @staticmethod
    def build_notification_html(title: str, content: str, app_name: Optional[str] = None) -> str:
        """
        构建通知邮件的 HTML 模板

        Args:
            title: 通知标题
            content: 通知内容
            app_name: 应用名称

        Returns:
            HTML 字符串
        """
        app = app_name or settings.APP_NAME
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f0f4f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1a73e8 0%,#0d47a1 100%);padding:32px 40px;">
              <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:0.5px;">{app}</h1>
            </td>
          </tr>
          <!-- Accent line -->
          <tr>
            <td style="height:3px;background:linear-gradient(90deg,#42a5f5,#1a73e8,#0d47a1);"></td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:36px 40px 32px;">
              <h2 style="margin:0 0 16px;color:#1a1a1a;font-size:18px;font-weight:600;">{title}</h2>
              <div style="color:#4a4a4a;font-size:14px;line-height:1.8;word-break:break-word;">{content}</div>
            </td>
          </tr>
          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <div style="border-top:1px solid #e8edf2;"></div>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px 24px;">
              <p style="margin:0;color:#9e9e9e;font-size:12px;text-align:center;line-height:1.6;">
                This email was sent by {app}. Please do not reply directly.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
