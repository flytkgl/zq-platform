#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编码生成器 Schema 定义
"""
from pydantic import BaseModel, Field


class CodeGenerateRequest(BaseModel):
    """编码生成请求"""
    prefix: str = Field(default="", description="前缀")
    separator: str = Field(default="", description="分隔符")
    generate_mode: str = Field(default="date_seq", description="生成模式: date_seq/datetime/random/snowflake/uuid/custom")
    date_format: str = Field(default="YYYYMMDD", description="日期格式")
    seq_length: int = Field(default=4, ge=1, le=10, description="序号长度")
    seq_reset_rule: str = Field(default="daily", description="序号重置规则: daily/monthly/yearly/never")
    random_length: int = Field(default=6, ge=4, le=20, description="随机字符长度")
    custom_template: str = Field(default="", description="自定义模板")
    business_type: str = Field(default="default", description="业务类型")


class CodeGenerateResponse(BaseModel):
    """编码生成响应"""
    code: str = Field(..., description="生成的编码")
