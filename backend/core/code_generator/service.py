#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编码生成器服务
"""
import logging
import random
import string
import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.code_generator.model import CodeSequence

logger = logging.getLogger(__name__)


class CodeGeneratorService:
    """编码生成器服务"""

    @staticmethod
    async def generate_code(
            db: AsyncSession,
            prefix: str = "",
            separator: str = "",
            generate_mode: str = "date_seq",
            date_format: str = "YYYYMMDD",
            seq_length: int = 4,
            seq_reset_rule: str = "daily",
            random_length: int = 6,
            custom_template: str = "",
            business_type: str = "default"
    ) -> str:
        """
        生成编码
        
        Args:
            db: 数据库会话
            prefix: 前缀
            separator: 分隔符
            generate_mode: 生成模式
            date_format: 日期格式
            seq_length: 序号长度
            seq_reset_rule: 序号重置规则
            random_length: 随机字符长度
            custom_template: 自定义模板
            business_type: 业务类型
            
        Returns:
            生成的编码
        """
        if generate_mode == "date_seq":
            return await CodeGeneratorService._generate_date_seq(
                db, prefix, separator, date_format, seq_length, seq_reset_rule, business_type
            )
        elif generate_mode == "datetime":
            return CodeGeneratorService._generate_datetime(prefix, separator)
        elif generate_mode == "random":
            return CodeGeneratorService._generate_random(prefix, separator, random_length)
        elif generate_mode == "snowflake":
            return CodeGeneratorService._generate_snowflake(prefix, separator)
        elif generate_mode == "uuid":
            return CodeGeneratorService._generate_uuid(prefix, separator)
        elif generate_mode == "custom":
            return await CodeGeneratorService._generate_custom(
                db, custom_template, prefix, separator, date_format, seq_length, seq_reset_rule, business_type
            )
        else:
            raise ValueError(f"不支持的生成模式: {generate_mode}")

    @staticmethod
    async def _generate_date_seq(
            db: AsyncSession,
            prefix: str,
            separator: str,
            date_format: str,
            seq_length: int,
            seq_reset_rule: str,
            business_type: str
    ) -> str:
        """生成日期+序号格式: PREFIX20241222-0001"""
        date_str = CodeGeneratorService._format_date(date_format)
        date_key = CodeGeneratorService._get_date_key(seq_reset_rule)
        
        # 获取或创建序号记录
        seq = await CodeGeneratorService._get_or_create_sequence(
            db, business_type, prefix, date_key
        )
        
        # 递增序号
        seq.current_seq += 1
        await db.commit()
        await db.refresh(seq)
        
        # 格式化序号
        seq_str = str(seq.current_seq).zfill(seq_length)
        
        # 组装编码
        parts = [prefix, date_str, seq_str] if prefix else [date_str, seq_str]
        return separator.join(parts)

    @staticmethod
    def _generate_datetime(prefix: str, separator: str) -> str:
        """生成日期时间格式: PREFIX20241222103000"""
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        
        if prefix:
            return f"{prefix}{separator}{datetime_str}"
        return datetime_str

    @staticmethod
    def _generate_random(prefix: str, separator: str, length: int) -> str:
        """生成随机字符格式: PREFIX-X7K9M2"""
        chars = string.ascii_uppercase + string.digits
        random_str = ''.join(random.choices(chars, k=length))
        
        if prefix:
            return f"{prefix}{separator}{random_str}"
        return random_str

    @staticmethod
    def _generate_snowflake(prefix: str, separator: str) -> str:
        """生成雪花ID格式: PREFIX1234567890123456"""
        # 简化版雪花ID：时间戳(42位) + 随机数(22位)
        timestamp = int(datetime.now().timestamp() * 1000)
        random_part = random.randint(0, 4194303)  # 22位随机数
        snowflake_id = (timestamp << 22) | random_part
        
        if prefix:
            return f"{prefix}{separator}{snowflake_id}"
        return str(snowflake_id)

    @staticmethod
    def _generate_uuid(prefix: str, separator: str) -> str:
        """生成UUID片段格式: PREFIX-a1b2c3d4"""
        uuid_str = str(uuid.uuid4()).replace('-', '')[:8]
        
        if prefix:
            return f"{prefix}{separator}{uuid_str}"
        return uuid_str

    @staticmethod
    async def _generate_custom(
            db: AsyncSession,
            template: str,
            prefix: str,
            separator: str,
            date_format: str,
            seq_length: int,
            seq_reset_rule: str,
            business_type: str
    ) -> str:
        """
        生成自定义模板格式
        支持的占位符:
        - {PREFIX}: 前缀
        - {DATE}: 日期
        - {SEQ}: 序号
        - {RANDOM:n}: n位随机字符
        - {UUID}: UUID片段
        """
        if not template:
            return await CodeGeneratorService._generate_date_seq(
                db, prefix, separator, date_format, seq_length, seq_reset_rule, business_type
            )
        
        result = template
        
        # 替换前缀
        if "{PREFIX}" in result:
            result = result.replace("{PREFIX}", prefix)
        
        # 替换日期
        if "{DATE}" in result:
            date_str = CodeGeneratorService._format_date(date_format)
            result = result.replace("{DATE}", date_str)
        
        # 替换序号
        if "{SEQ}" in result:
            date_key = CodeGeneratorService._get_date_key(seq_reset_rule)
            seq = await CodeGeneratorService._get_or_create_sequence(
                db, business_type, prefix, date_key
            )
            seq.current_seq += 1
            await db.commit()
            await db.refresh(seq)
            seq_str = str(seq.current_seq).zfill(seq_length)
            result = result.replace("{SEQ}", seq_str)
        
        # 替换随机字符
        import re
        random_pattern = r'\{RANDOM:(\d+)\}'
        for match in re.finditer(random_pattern, result):
            length = int(match.group(1))
            chars = string.ascii_uppercase + string.digits
            random_str = ''.join(random.choices(chars, k=length))
            result = result.replace(match.group(0), random_str)
        
        # 替换UUID
        if "{UUID}" in result:
            uuid_str = str(uuid.uuid4()).replace('-', '')[:8]
            result = result.replace("{UUID}", uuid_str)
        
        return result

    @staticmethod
    def _format_date(date_format: str) -> str:
        """格式化日期"""
        now = datetime.now()
        
        # 转换前端格式到Python格式（长 token 必须先替换，避免 YYYY 被 YY 截断）
        replacements = [
            ("YYYY", "%Y"),
            ("YY", "%y"),
            ("MM", "%m"),
            ("DD", "%d"),
            ("HH", "%H"),
            ("mm", "%M"),
            ("ss", "%S"),
        ]
        
        python_format = date_format
        for key, value in replacements:
            python_format = python_format.replace(key, value)
        
        return now.strftime(python_format)

    @staticmethod
    def _get_date_key(reset_rule: str) -> str:
        """获取日期键（用于序号重置）"""
        now = datetime.now()
        
        if reset_rule == "daily":
            return now.strftime("%Y%m%d")
        elif reset_rule == "monthly":
            return now.strftime("%Y%m")
        elif reset_rule == "yearly":
            return now.strftime("%Y")
        else:  # never
            return ""

    @staticmethod
    async def _get_or_create_sequence(
            db: AsyncSession,
            business_type: str,
            prefix: str,
            date_key: str
    ) -> CodeSequence:
        """获取或创建序号记录"""
        stmt = select(CodeSequence).where(
            and_(
                CodeSequence.business_type == business_type,
                CodeSequence.prefix == prefix,
                CodeSequence.date_key == date_key,
                CodeSequence.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        seq = result.scalar_one_or_none()
        
        if not seq:
            seq = CodeSequence(
                business_type=business_type,
                prefix=prefix,
                date_key=date_key,
                current_seq=0
            )
            db.add(seq)
            await db.flush()
        
        return seq
