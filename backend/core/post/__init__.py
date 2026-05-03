#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post Module - 岗位管理模块
"""
from core.post.model import Post
from core.post.service import PostService
from core.post.api import router

__all__ = ["Post", "PostService", "router"]
