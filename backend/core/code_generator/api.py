#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编码生成器 API
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from core.code_generator.schema import CodeGenerateRequest, CodeGenerateResponse
from core.code_generator.service import CodeGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code-generator", tags=["编码生成器"])


@router.post("/generate", response_model=CodeGenerateResponse, summary="生成编码")
async def generate_code(
        request: CodeGenerateRequest,
        db: AsyncSession = Depends(get_db),
):
    """
    生成编码
    
    支持的生成模式:
    - date_seq: 日期+序号 (PREFIX20241222-0001)
    - datetime: 日期时间 (PREFIX20241222103000)
    - random: 随机字符 (PREFIX-X7K9M2)
    - snowflake: 雪花ID (PREFIX1234567890123456)
    - uuid: UUID片段 (PREFIX-a1b2c3d4)
    - custom: 自定义模板
    """
    code = await CodeGeneratorService.generate_code(
        db=db,
        prefix=request.prefix,
        separator=request.separator,
        generate_mode=request.generate_mode,
        date_format=request.date_format,
        seq_length=request.seq_length,
        seq_reset_rule=request.seq_reset_rule,
        random_length=request.random_length,
        custom_template=request.custom_template,
        business_type=request.business_type
    )
    
    return CodeGenerateResponse(code=code)
