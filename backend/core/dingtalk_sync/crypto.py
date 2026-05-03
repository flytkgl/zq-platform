#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉回调加解密工具

实现钉钉事件订阅所需的签名验证和消息加解密。
基于钉钉官方文档：https://open.dingtalk.com/document/orgapp/callback-overview

加密方案：AES-CBC，PKCS#7 padding，key 由 aes_key + "=" base64 解码得到
签名方案：SHA1(token + timestamp + nonce + encrypt)
"""
import base64
import hashlib
import secrets
import struct
import time
from typing import Dict

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class DingtalkCrypto:
    """钉钉回调消息加解密"""

    def __init__(self, token: str, aes_key: str, corp_id: str):
        self.token = token
        self.corp_id = corp_id
        self.aes_key_bytes = base64.b64decode(aes_key + "=")

    def _generate_nonce(self, length: int = 16) -> str:
        return secrets.token_hex(length // 2)

    def _pkcs7_pad(self, data: bytes, block_size: int = 32) -> bytes:
        padding_len = block_size - (len(data) % block_size)
        return data + bytes([padding_len] * padding_len)

    def _pkcs7_unpad(self, data: bytes) -> bytes:
        padding_len = data[-1]
        return data[:-padding_len]

    def _sign(self, token: str, timestamp: str, nonce: str, encrypt: str) -> str:
        """计算签名 SHA1(sort(token, timestamp, nonce, encrypt))"""
        parts = sorted([token, timestamp, nonce, encrypt])
        raw = "".join(parts).encode("utf-8")
        return hashlib.sha1(raw).hexdigest()

    def encrypt(self, plaintext: str) -> Dict[str, str]:
        """
        加密明文消息，返回回调响应体

        返回: {"msg_signature": ..., "timeStamp": ..., "nonce": ..., "encrypt": ...}
        """
        nonce = self._generate_nonce()
        timestamp = str(int(time.time()))

        # 16字节随机字符串 + 4字节网络序消息长度 + 明文 + corp_id
        random_bytes = secrets.token_bytes(16)
        text_bytes = plaintext.encode("utf-8")
        corp_id_bytes = self.corp_id.encode("utf-8")
        content = random_bytes + struct.pack("!I", len(text_bytes)) + text_bytes + corp_id_bytes

        # AES-CBC 加密
        padded = self._pkcs7_pad(content)
        iv = self.aes_key_bytes[:16]
        cipher = Cipher(algorithms.AES(self.aes_key_bytes), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        encrypt_str = base64.b64encode(encrypted).decode("utf-8")
        signature = self._sign(self.token, timestamp, nonce, encrypt_str)

        return {
            "msg_signature": signature,
            "timeStamp": timestamp,
            "nonce": nonce,
            "encrypt": encrypt_str,
        }

    def decrypt(self, encrypt_str: str) -> str:
        """解密密文，返回明文 JSON 字符串，并校验 corp_id"""
        encrypted = base64.b64decode(encrypt_str)

        iv = self.aes_key_bytes[:16]
        cipher = Cipher(algorithms.AES(self.aes_key_bytes), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted) + decryptor.finalize()

        unpadded = self._pkcs7_unpad(decrypted)

        msg_len = struct.unpack("!I", unpadded[16:20])[0]
        plaintext = unpadded[20:20 + msg_len].decode("utf-8")

        receive_id = unpadded[20 + msg_len:].decode("utf-8")
        if receive_id != self.corp_id:
            raise ValueError(f"corp_id 校验失败: 期望 {self.corp_id}，实际 {receive_id}")

        return plaintext

    def verify_signature(self, msg_signature: str, timestamp: str, nonce: str, encrypt: str) -> bool:
        """验证回调签名"""
        calculated = self._sign(self.token, timestamp, nonce, encrypt)
        return calculated == msg_signature

    def handle_callback(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        encrypt: str,
    ) -> str:
        """
        处理回调：验签 + 解密

        返回解密后的明文 JSON 字符串
        """
        if not self.verify_signature(msg_signature, timestamp, nonce, encrypt):
            raise ValueError("签名验证失败")
        return self.decrypt(encrypt)

    def generate_success_response(self) -> Dict[str, str]:
        """生成回调成功响应（加密 "success"）"""
        return self.encrypt("success")
