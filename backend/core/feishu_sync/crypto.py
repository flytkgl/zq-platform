#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书回调加解密工具

实现飞书事件订阅所需的签名验证和消息解密。
飞书文档：https://open.feishu.cn/document/server-docs/event-subscription-guide/event-subscription-configure-/encrypt-key-encryption-configuration-case

加密方案：AES-256-CBC，密钥 = SHA256(encrypt_key)，IV 为密文前16字节
签名方案：SHA256(timestamp + nonce + encrypt_key + body)
"""
import hashlib
import json
from typing import Any, Dict

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class FeishuCrypto:
    """飞书回调消息加解密"""

    def __init__(self, encrypt_key: str, verification_token: str):
        self.encrypt_key = encrypt_key
        self.verification_token = verification_token
        self._aes_key = hashlib.sha256(encrypt_key.encode("utf-8")).digest() if encrypt_key else None

    def decrypt(self, encrypt_str: str) -> str:
        """
        解密飞书加密消息

        飞书加密格式：base64(iv + AES-256-CBC(plaintext))
        - 前16字节为IV
        - 其余为密文（PKCS7 padding 已包含在内）
        """
        if not self._aes_key:
            raise ValueError("encrypt_key 未配置，无法解密")

        import base64
        encrypted = base64.b64decode(encrypt_str)

        iv = encrypted[:16]
        cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted[16:]) + decryptor.finalize()

        # PKCS7 unpad with validation
        if not decrypted:
            raise ValueError("解密结果为空")
        padding_len = decrypted[-1]
        if padding_len < 1 or padding_len > 16 or padding_len > len(decrypted):
            raise ValueError(f"PKCS7 填充长度无效: {padding_len}")
        plaintext = decrypted[:-padding_len]

        return plaintext.decode("utf-8")

    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str) -> bool:
        """
        验证飞书回调签名
        SHA256(timestamp + nonce + encrypt_key + body) == X-Lark-Signature
        """
        raw = f"{timestamp}{nonce}{self.encrypt_key}{body}"
        calculated = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return calculated == signature

    def decrypt_event(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        解密事件体：如果 body 包含 encrypt 字段，先解密再解析 JSON
        """
        if "encrypt" in body:
            plaintext = self.decrypt(body["encrypt"])
            return json.loads(plaintext)
        return body

    def handle_url_verification(self, body: Dict[str, Any]) -> Dict[str, str]:
        """
        处理 URL 验证请求
        飞书发送 {"challenge":"xxx","token":"xxx","type":"url_verification"}
        需返回 {"challenge":"xxx"}
        """
        token = body.get("token", "")
        if token != self.verification_token:
            raise ValueError(f"verification_token 校验失败: 期望 {self.verification_token}，实际 {token}")
        return {"challenge": body.get("challenge", "")}
