"""
短信发送工具

支持两种短信服务商：
1. 阿里云短信 (Alibaba Cloud SMS) - 使用 HTTP API + HMAC-SHA1 签名
2. 腾讯云短信 (Tencent Cloud SMS) - 使用 HTTP API + HMAC-SHA256 签名

配置通过 config_manager 三级获取（Redis → 数据库 → env）
"""
import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AliyunSMS:
    """阿里云短信服务"""

    API_URL = "https://dysmsapi.aliyuncs.com"

    @staticmethod
    async def _get_config() -> dict:
        """通过 config_manager 三级获取阿里云短信配置"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_sms")
        return {
            "provider": group_config.get("provider") or "aliyun",
            "access_key_id": group_config.get("aliyun_access_key_id") or None,
            "access_key_secret": group_config.get("aliyun_access_key_secret") or None,
            "sign_name": group_config.get("aliyun_sign_name") or None,
            "template_code": group_config.get("aliyun_template_code") or None,
        }

    @staticmethod
    async def is_configured_async() -> bool:
        """检查阿里云短信是否已配置"""
        config = await AliyunSMS._get_config()
        return bool(
            config["access_key_id"]
            and config["access_key_secret"]
            and config["sign_name"]
            and config["template_code"]
        )

    @staticmethod
    def _percent_encode(s: str) -> str:
        """阿里云特殊 URL 编码"""
        return quote_plus(s, safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def _sign(params: dict, access_key_secret: str) -> str:
        """计算阿里云 API 签名"""
        sorted_params = sorted(params.items())
        canonicalized = "&".join(
            f"{AliyunSMS._percent_encode(k)}={AliyunSMS._percent_encode(str(v))}"
            for k, v in sorted_params
        )
        string_to_sign = f"GET&%2F&{AliyunSMS._percent_encode(canonicalized)}"
        sign_key = f"{access_key_secret}&"
        hmac_hash = hmac.new(
            sign_key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(hmac_hash).decode("utf-8")

    @staticmethod
    async def send(
            phone_numbers: List[str],
            template_param: Optional[Dict[str, str]] = None,
    ) -> Dict[str, bool]:
        """
        发送短信

        Args:
            phone_numbers: 手机号列表
            template_param: 模板参数，如 {"title": "审批通知", "content": "您有一条待审批任务"}

        Returns:
            {phone: success} 字典
        """
        config = await AliyunSMS._get_config()
        if not config["access_key_id"]:
            logger.warning("阿里云短信未配置，跳过发送")
            return {phone: False for phone in phone_numbers}

        results = {}
        for phone in phone_numbers:
            try:
                params = {
                    "AccessKeyId": config["access_key_id"],
                    "Action": "SendSms",
                    "Format": "JSON",
                    "PhoneNumbers": phone,
                    "RegionId": "cn-hangzhou",
                    "SignName": config["sign_name"],
                    "SignatureMethod": "HMAC-SHA1",
                    "SignatureNonce": str(uuid.uuid4()),
                    "SignatureVersion": "1.0",
                    "TemplateCode": config["template_code"],
                    "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "Version": "2017-05-25",
                }
                if template_param:
                    params["TemplateParam"] = json.dumps(template_param, ensure_ascii=False)

                signature = AliyunSMS._sign(params, config["access_key_secret"])
                params["Signature"] = signature

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(AliyunSMS.API_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                if data.get("Code") == "OK":
                    results[phone] = True
                    logger.info(f"阿里云短信发送成功: {phone}")
                else:
                    results[phone] = False
                    logger.warning(f"阿里云短信发送失败: {phone}, Code={data.get('Code')}, Message={data.get('Message')}")
            except Exception as e:
                results[phone] = False
                logger.error(f"阿里云短信发送异常: {phone}, {e}")

        return results


class TencentSMS:
    """腾讯云短信服务"""

    API_URL = "https://sms.tencentcloudapi.com"
    SERVICE = "sms"
    VERSION = "2021-01-11"
    ACTION = "SendSms"

    @staticmethod
    async def _get_config() -> dict:
        """通过 config_manager 三级获取腾讯云短信配置"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_sms")
        return {
            "provider": group_config.get("provider") or "aliyun",
            "secret_id": group_config.get("tencent_secret_id") or None,
            "secret_key": group_config.get("tencent_secret_key") or None,
            "sdk_app_id": group_config.get("tencent_sdk_app_id") or None,
            "sign_name": group_config.get("tencent_sign_name") or None,
            "template_id": group_config.get("tencent_template_id") or None,
        }

    @staticmethod
    async def is_configured_async() -> bool:
        """检查腾讯云短信是否已配置"""
        config = await TencentSMS._get_config()
        return bool(
            config["secret_id"]
            and config["secret_key"]
            and config["sdk_app_id"]
            and config["sign_name"]
            and config["template_id"]
        )

    @staticmethod
    def _sign_v3(secret_key: str, date: str, service: str, string_to_sign: str) -> str:
        """腾讯云 TC3-HMAC-SHA256 签名"""

        def _hmac_sha256(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _hmac_sha256(f"TC3{secret_key}".encode("utf-8"), date)
        secret_service = _hmac_sha256(secret_date, service)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        return hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    async def send(
            phone_numbers: List[str],
            template_param_set: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """
        发送短信

        Args:
            phone_numbers: 手机号列表（需带国际区号前缀，如 +86）
            template_param_set: 模板参数列表，如 ["审批通知", "您有一条待审批任务"]

        Returns:
            {phone: success} 字典
        """
        config = await TencentSMS._get_config()
        if not config["secret_id"]:
            logger.warning("腾讯云短信未配置，跳过发送")
            return {phone: False for phone in phone_numbers}

        # 腾讯云手机号需要 +86 前缀
        formatted_phones = []
        for phone in phone_numbers:
            if not phone.startswith("+"):
                phone = f"+86{phone}"
            formatted_phones.append(phone)

        payload = {
            "SmsSdkAppId": config["sdk_app_id"],
            "SignName": config["sign_name"],
            "TemplateId": config["template_id"],
            "PhoneNumberSet": formatted_phones,
        }
        if template_param_set:
            payload["TemplateParamSet"] = template_param_set

        payload_json = json.dumps(payload)

        # 构建签名
        now = int(time.time())
        date = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")

        # CanonicalRequest
        hashed_payload = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        canonical_request = (
            f"POST\n/\n\n"
            f"content-type:application/json; charset=utf-8\n"
            f"host:sms.tencentcloudapi.com\n\n"
            f"content-type;host\n"
            f"{hashed_payload}"
        )

        # StringToSign
        credential_scope = f"{date}/{TencentSMS.SERVICE}/tc3_request"
        hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"TC3-HMAC-SHA256\n{now}\n{credential_scope}\n{hashed_canonical}"

        # Signature
        signature = TencentSMS._sign_v3(config["secret_key"], date, TencentSMS.SERVICE, string_to_sign)

        # Authorization
        authorization = (
            f"TC3-HMAC-SHA256 "
            f"Credential={config['secret_id']}/{credential_scope}, "
            f"SignedHeaders=content-type;host, "
            f"Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": "sms.tencentcloudapi.com",
            "X-TC-Action": TencentSMS.ACTION,
            "X-TC-Version": TencentSMS.VERSION,
            "X-TC-Timestamp": str(now),
        }

        results = {phone: False for phone in phone_numbers}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(TencentSMS.API_URL, headers=headers, content=payload_json)
                resp.raise_for_status()
                data = resp.json()

            response = data.get("Response", {})
            if "Error" in response:
                logger.error(
                    f"腾讯云短信发送失败: Code={response['Error'].get('Code')}, "
                    f"Message={response['Error'].get('Message')}"
                )
                return results

            send_status_set = response.get("SendStatusSet", [])
            for i, status in enumerate(send_status_set):
                original_phone = phone_numbers[i] if i < len(phone_numbers) else "unknown"
                if status.get("Code") == "Ok":
                    results[original_phone] = True
                    logger.info(f"腾讯云短信发送成功: {original_phone}")
                else:
                    logger.warning(
                        f"腾讯云短信发送失败: {original_phone}, "
                        f"Code={status.get('Code')}, Message={status.get('Message')}"
                    )
        except Exception as e:
            logger.error(f"腾讯云短信发送异常: {e}")

        return results


class SMSSender:
    """
    统一短信发送器

    根据配置的 provider 自动选择阿里云或腾讯云
    """

    @staticmethod
    async def _get_provider() -> str:
        """获取当前配置的短信服务商"""
        from app.config_manager import config_manager
        group_config = await config_manager.get_group("notify_sms")
        return group_config.get("provider") or "aliyun"

    @staticmethod
    async def is_configured_async() -> bool:
        """检查短信服务是否已配置"""
        provider = await SMSSender._get_provider()
        if provider == "tencent":
            return await TencentSMS.is_configured_async()
        return await AliyunSMS.is_configured_async()

    @staticmethod
    async def send(
            phone_numbers: List[str],
            title: str,
            content: str,
    ) -> Dict[str, bool]:
        """
        发送短信通知

        Args:
            phone_numbers: 手机号列表
            title: 通知标题
            content: 通知内容

        Returns:
            {phone: success} 字典
        """
        if not phone_numbers:
            return {}

        provider = await SMSSender._get_provider()

        if provider == "tencent":
            return await TencentSMS.send(
                phone_numbers=phone_numbers,
                template_param_set=[title, content],
            )
        else:
            return await AliyunSMS.send(
                phone_numbers=phone_numbers,
                template_param={"title": title, "content": content},
            )
