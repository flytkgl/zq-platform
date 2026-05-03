#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钉钉通讯录 API 客户端
封装钉钉开放平台部门和用户相关接口
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

DINGTALK_API_BASE = "https://oapi.dingtalk.com"


class DingtalkClient:
    """钉钉通讯录 API 客户端"""

    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def get_access_token(self) -> str:
        """获取 access_token（带内存缓存，提前 5 分钟过期）"""
        now = time.time()
        if self._access_token and now < self._token_expires_at:
            return self._access_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{DINGTALK_API_BASE}/gettoken",
                params={"appkey": self.app_key, "appsecret": self.app_secret},
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("errcode") != 0:
                raise Exception(f"获取钉钉 access_token 失败: {result.get('errmsg', result)}")

            self._access_token = result["access_token"]
            self._token_expires_at = now + result.get("expires_in", 7200) - 300
            return self._access_token

    async def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """带 access_token 的 POST 请求"""
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{DINGTALK_API_BASE}{path}",
                params={"access_token": token},
                json=body,
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("errcode") != 0:
                raise Exception(f"钉钉 API 调用失败 [{path}]: {result.get('errmsg', result)}")
            return result

    # ==================== 连接测试 ====================

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接：获取 token + 拉取根部门信息验证
        返回根部门名称等基本信息
        """
        await self.get_access_token()
        result = await self._post("/topapi/v2/department/get", {"dept_id": 1})
        dept_info = result.get("result", {})
        return {
            "success": True,
            "corp_name": dept_info.get("name", ""),
            "dept_id": dept_info.get("dept_id"),
        }

    # ==================== 部门 API ====================

    async def get_dept_list(self, dept_id: int = 1) -> List[Dict[str, Any]]:
        """
        获取子部门列表
        https://open.dingtalk.com/document/orgapp/obtain-the-department-list-v2
        """
        result = await self._post(
            "/topapi/v2/department/listsub",
            {"dept_id": dept_id},
        )
        return result.get("result", [])

    async def get_dept_detail(self, dept_id: int) -> Dict[str, Any]:
        """获取部门详情"""
        result = await self._post(
            "/topapi/v2/department/get",
            {"dept_id": dept_id},
        )
        return result.get("result", {})

    async def get_all_depts(self, root_dept_id: int = 1) -> List[Dict[str, Any]]:
        """
        递归获取指定根部门下的全量部门列表（广度优先）
        返回扁平列表，包含 parent_id 信息
        """
        all_depts = []
        queue = [root_dept_id]

        while queue:
            current_dept_id = queue.pop(0)

            if current_dept_id != root_dept_id:
                detail = await self.get_dept_detail(current_dept_id)
                detail["parent_dept_id"] = detail.get("parent_id", root_dept_id)
                all_depts.append(detail)

            children = await self.get_dept_list(current_dept_id)
            for child in children:
                child_id = child.get("dept_id")
                if child_id:
                    queue.append(child_id)

        return all_depts

    async def get_dept_tree(self, root_dept_id: int = 1) -> List[Dict[str, Any]]:
        """
        获取部门树形结构（供前端选择同步范围）
        """
        children = await self.get_dept_list(root_dept_id)
        tree = []
        for child in children:
            node = {
                "dept_id": child.get("dept_id"),
                "name": child.get("name"),
                "children": await self.get_dept_tree(child.get("dept_id")),
            }
            tree.append(node)
        return tree

    # ==================== 用户 API ====================

    async def get_user_list(self, dept_id: int, cursor: int = 0, size: int = 100) -> Dict[str, Any]:
        """
        获取部门用户列表（分页）
        https://open.dingtalk.com/document/orgapp/queries-the-complete-information-of-a-department-user
        """
        result = await self._post(
            "/topapi/v2/user/list",
            {"dept_id": dept_id, "cursor": cursor, "size": size},
        )
        return result.get("result", {})

    async def get_all_users_in_dept(self, dept_id: int) -> List[Dict[str, Any]]:
        """获取部门下所有用户（自动翻页）"""
        users = []
        cursor = 0

        while True:
            page = await self.get_user_list(dept_id, cursor=cursor)
            page_list = page.get("list", [])
            users.extend(page_list)

            if not page.get("has_more", False):
                break
            cursor = page.get("next_cursor", 0)

        return users

    async def get_user_detail(self, userid: str) -> Dict[str, Any]:
        """获取用户详情"""
        result = await self._post(
            "/topapi/v2/user/get",
            {"userid": userid},
        )
        return result.get("result", {})

    # ==================== 回调注册 API ====================

    async def register_callback(
        self,
        callback_url: str,
        callback_tag: List[str],
        token: str,
        aes_key: str,
    ) -> Dict[str, Any]:
        """
        注册事件回调
        https://open.dingtalk.com/document/orgapp/registers-an-event-callback-interface
        """
        return await self._post(
            "/call_back/register_call_back",
            {
                "call_back_tag": callback_tag,
                "token": token,
                "aes_key": aes_key,
                "url": callback_url,
            },
        )

    async def update_callback(
        self,
        callback_url: str,
        callback_tag: List[str],
        token: str,
        aes_key: str,
    ) -> Dict[str, Any]:
        """更新事件回调"""
        return await self._post(
            "/call_back/update_call_back",
            {
                "call_back_tag": callback_tag,
                "token": token,
                "aes_key": aes_key,
                "url": callback_url,
            },
        )

    async def delete_callback(self) -> Dict[str, Any]:
        """删除事件回调"""
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DINGTALK_API_BASE}/call_back/delete_call_back",
                params={"access_token": token},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") != 0:
                raise Exception(f"删除回调失败: {result.get('errmsg', result)}")
            return result

    async def get_callback(self) -> Dict[str, Any]:
        """查询已注册的事件回调"""
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{DINGTALK_API_BASE}/call_back/get_call_back",
                params={"access_token": token},
            )
            resp.raise_for_status()
            return resp.json()
