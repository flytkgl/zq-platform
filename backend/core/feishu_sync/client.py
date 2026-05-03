#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书通讯录 API 客户端
封装飞书开放平台部门和用户相关接口
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


class FeishuClient:
    """飞书通讯录 API 客户端"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tenant_access_token: Optional[str] = None
        self._token_expires_at: float = 0

    async def get_tenant_access_token(self) -> str:
        """获取 tenant_access_token（带内存缓存，提前 5 分钟过期）"""
        now = time.time()
        if self._tenant_access_token and now < self._token_expires_at:
            return self._tenant_access_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 0:
                raise Exception(f"获取飞书 tenant_access_token 失败: {result.get('msg', result)}")

            self._tenant_access_token = result["tenant_access_token"]
            self._token_expires_at = now + result.get("expire", 7200) - 300
            return self._tenant_access_token

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """带 Bearer token 的 GET 请求"""
        token = await self.get_tenant_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{FEISHU_API_BASE}{path}",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 0:
                raise Exception(f"飞书 API 调用失败 [{path}]: {result.get('msg', result)}")
            return result

    async def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """带 Bearer token 的 POST 请求"""
        token = await self.get_tenant_access_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{FEISHU_API_BASE}{path}",
                json=body,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 0:
                raise Exception(f"飞书 API 调用失败 [{path}]: {result.get('msg', result)}")
            return result

    # ==================== 连接测试 ====================

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接：获取 token + 拉取根部门信息验证"""
        await self.get_tenant_access_token()
        result = await self._get("/contact/v3/departments/0", {
            "department_id_type": "open_department_id",
        })
        dept_info = result.get("data", {}).get("department", {})
        return {
            "success": True,
            "corp_name": dept_info.get("name", ""),
            "dept_id": dept_info.get("open_department_id", "0"),
        }

    # ==================== 部门 API ====================

    async def get_dept_children(
        self,
        dept_id: str = "0",
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取子部门列表（分页）
        https://open.feishu.cn/document/server-docs/contact-v3/department/children
        """
        params: Dict[str, Any] = {
            "department_id_type": "open_department_id",
            "page_size": page_size,
        }
        if page_token:
            params["page_token"] = page_token

        result = await self._get(f"/contact/v3/departments/{dept_id}/children", params)
        return result.get("data", {})

    async def get_dept_detail(self, dept_id: str) -> Dict[str, Any]:
        """获取部门详情"""
        result = await self._get(f"/contact/v3/departments/{dept_id}", {
            "department_id_type": "open_department_id",
        })
        return result.get("data", {}).get("department", {})

    async def get_all_depts(self, root_dept_id: str = "0") -> List[Dict[str, Any]]:
        """
        递归获取指定根部门下的全量部门列表（广度优先 + 自动分页）
        返回扁平列表，包含 parent_department_id 信息
        """
        all_depts: List[Dict[str, Any]] = []
        queue = [root_dept_id]

        while queue:
            current_dept_id = queue.pop(0)
            page_token = None

            while True:
                data = await self.get_dept_children(current_dept_id, page_size=50, page_token=page_token)
                items = data.get("items", [])
                for item in items:
                    all_depts.append(item)
                    child_id = item.get("open_department_id")
                    if child_id:
                        queue.append(child_id)

                if not data.get("has_more", False):
                    break
                page_token = data.get("page_token")

        return all_depts

    async def get_dept_tree(self, root_dept_id: str = "0") -> List[Dict[str, Any]]:
        """获取部门树形结构（供前端选择同步范围）"""
        all_depts = await self.get_all_depts(root_dept_id)

        dept_map: Dict[str, Dict[str, Any]] = {}
        for d in all_depts:
            did = d.get("open_department_id", "")
            dept_map[did] = {
                "dept_id": did,
                "name": d.get("name", ""),
                "parent_department_id": d.get("parent_department_id", "0"),
                "children": [],
            }

        tree: List[Dict[str, Any]] = []
        for d in dept_map.values():
            parent_id = d["parent_department_id"]
            if parent_id in dept_map and parent_id != d["dept_id"]:
                dept_map[parent_id]["children"].append(d)
            else:
                tree.append(d)

        return tree

    # ==================== 用户 API ====================

    async def get_user_list(
        self,
        dept_id: str,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取部门用户列表（分页）
        https://open.feishu.cn/document/server-docs/contact-v3/user/find_by_department
        """
        params: Dict[str, Any] = {
            "department_id": dept_id,
            "department_id_type": "open_department_id",
            "page_size": page_size,
        }
        if page_token:
            params["page_token"] = page_token

        result = await self._get("/contact/v3/users/find_by_department", params)
        return result.get("data", {})

    async def get_all_users_in_dept(self, dept_id: str) -> List[Dict[str, Any]]:
        """获取部门下所有用户（自动翻页）"""
        users: List[Dict[str, Any]] = []
        page_token = None

        while True:
            data = await self.get_user_list(dept_id, page_size=50, page_token=page_token)
            items = data.get("items", [])
            users.extend(items)

            if not data.get("has_more", False):
                break
            page_token = data.get("page_token")

        return users

    async def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """获取用户详情"""
        result = await self._get(f"/contact/v3/users/{user_id}", {
            "department_id_type": "open_department_id",
        })
        return result.get("data", {}).get("user", {})
