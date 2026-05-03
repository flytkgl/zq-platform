#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业微信通讯录 API 客户端
封装企业微信开放平台部门和成员相关接口
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

WECOM_API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"


class WecomClient:
    """企业微信通讯录 API 客户端"""

    def __init__(self, corp_id: str, corp_secret: str):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def get_access_token(self) -> str:
        """获取 access_token（带内存缓存，提前 5 分钟过期）"""
        now = time.time()
        if self._access_token and now < self._token_expires_at:
            return self._access_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{WECOM_API_BASE}/gettoken",
                params={"corpid": self.corp_id, "corpsecret": self.corp_secret},
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("errcode") != 0:
                raise Exception(f"获取企业微信 access_token 失败: {result.get('errmsg', result)}")

            self._access_token = result["access_token"]
            self._token_expires_at = now + result.get("expires_in", 7200) - 300
            return self._access_token

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """带 access_token 的 GET 请求"""
        token = await self.get_access_token()
        all_params = {"access_token": token}
        if params:
            all_params.update(params)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{WECOM_API_BASE}{path}", params=all_params)
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                raise Exception(f"企业微信 API 调用失败 [{path}]: {result.get('errmsg', result)}")
            return result

    async def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """带 access_token 的 POST 请求"""
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{WECOM_API_BASE}{path}",
                params={"access_token": token},
                json=body,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                raise Exception(f"企业微信 API 调用失败 [{path}]: {result.get('errmsg', result)}")
            return result

    # ==================== 连接测试 ====================

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接：获取 token + 拉取根部门信息验证"""
        await self.get_access_token()
        result = await self._get("/department/list", {"id": 1})
        dept_list = result.get("department", [])
        root_name = ""
        for d in dept_list:
            if d.get("id") == 1:
                root_name = d.get("name", "")
                break
        return {
            "success": True,
            "corp_name": root_name,
            "dept_count": len(dept_list),
        }

    # ==================== 部门 API ====================

    async def get_dept_list(self, dept_id: int = 1) -> List[Dict[str, Any]]:
        """
        获取部门列表
        https://developer.work.weixin.qq.com/document/path/90208
        """
        result = await self._get("/department/list", {"id": dept_id})
        return result.get("department", [])

    async def get_dept_detail(self, dept_id: int) -> Dict[str, Any]:
        """获取单个部门详情"""
        result = await self._get("/department/get", {"id": dept_id})
        return result.get("department", {})

    async def get_all_depts(self, root_dept_id: int = 1) -> List[Dict[str, Any]]:
        """
        获取指定根部门下的全量部门列表
        企业微信 /department/list 返回指定部门及所有子部门（递归），结果扁平
        """
        all_depts = await self.get_dept_list(root_dept_id)
        return [d for d in all_depts if d.get("id") != root_dept_id]

    async def get_dept_tree(self, root_dept_id: int = 1) -> List[Dict[str, Any]]:
        """获取部门树形结构（供前端选择同步范围）"""
        all_depts = await self.get_dept_list(root_dept_id)

        dept_map: Dict[int, Dict[str, Any]] = {}
        for d in all_depts:
            dept_map[d["id"]] = {
                "dept_id": d["id"],
                "name": d.get("name", ""),
                "parentid": d.get("parentid", 0),
                "children": [],
            }

        tree: List[Dict[str, Any]] = []
        for d in dept_map.values():
            parent_id = d["parentid"]
            if parent_id in dept_map and parent_id != d["dept_id"]:
                dept_map[parent_id]["children"].append(d)
            elif d["dept_id"] == root_dept_id:
                tree.append(d)
            else:
                tree.append(d)

        return tree

    # ==================== 用户/成员 API ====================

    async def get_user_list(self, dept_id: int) -> List[Dict[str, Any]]:
        """
        获取部门成员详情列表
        https://developer.work.weixin.qq.com/document/path/90201
        """
        result = await self._get("/user/list", {"department_id": dept_id})
        return result.get("userlist", [])

    async def get_user_detail(self, userid: str) -> Dict[str, Any]:
        """获取成员详情"""
        return await self._get("/user/get", {"userid": userid})

    # ==================== 回调注册 API ====================

    async def create_callback(
        self,
        callback_url: str,
        callback_tag: List[str],
        token: str,
        aes_key: str,
    ) -> Dict[str, Any]:
        """
        注册事件回调
        https://developer.work.weixin.qq.com/document/path/90930
        """
        # 企业微信的回调设置不是通过API注册的，而是在管理后台配置
        # 这里提供一个验证URL有效性的接口（回调模式验证由 callback 端点的 GET 处理）
        return {"errcode": 0, "errmsg": "ok"}

    async def delete_callback(self) -> Dict[str, Any]:
        """企业微信回调通过管理后台管理，这里仅做标记"""
        return {"errcode": 0, "errmsg": "ok"}

    async def get_callback(self) -> Dict[str, Any]:
        """查询回调设置状态"""
        return {"errcode": 0, "errmsg": "ok"}
