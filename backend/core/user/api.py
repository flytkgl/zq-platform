#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User API - 用户接口
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.base_schema import PaginatedResponse, ResponseModel
from core.user.schema import (
    UserCreate, UserUpdate, UserResponse, UserSimple, OrgChartNode, OrgChartChainNode,
    UserPasswordResetIn, UserPasswordSetIn,
    UserBatchDeleteIn, UserBatchDeleteOut,
    UserBatchUpdateStatusIn, UserBatchUpdateStatusOut,
    UserProfileUpdateIn
)
from core.user.service import UserService
from utils.security import get_current_user, get_current_user_id

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post("", response_model=UserResponse, summary="创建用户")
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建用户"""
    # 用户名唯一性校验
    if not await UserService.check_unique(db, field="username", value=data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 邮箱唯一性校验
    if data.email:
        if not await UserService.check_unique(db, field="email", value=data.email):
            raise HTTPException(status_code=400, detail="邮箱已存在")

    # 手机号唯一性校验
    if data.mobile:
        if not await UserService.check_unique(db, field="mobile", value=data.mobile):
            raise HTTPException(status_code=400, detail="手机号已存在")

    user = await UserService.create(db=db, data=data)

    # 构建响应并添加 role_ids
    user_dict = _build_user_response(user).model_dump()
    role_ids = await UserService.get_user_role_ids(db, user.id)
    user_dict['role_ids'] = role_ids
    return user_dict


@router.get("", response_model=PaginatedResponse[UserResponse], summary="获取用户列表")
async def get_user_list(
        page: int = Query(default=1, ge=1, description="页码"),
        page_size: int = Query(default=settings.PAGE_SIZE, ge=1, le=settings.PAGE_MAX_SIZE, alias="pageSize",
                               description="每页数量"),
        name: Optional[str] = Query(None, description="姓名"),
        username: Optional[str] = Query(None, description="用户名"),
        mobile: Optional[str] = Query(None, description="手机号"),
        email: Optional[str] = Query(None, description="邮箱"),
        user_status: Optional[int] = Query(None, alias="user_status", description="用户状态"),
        user_type: Optional[int] = Query(None, alias="user_type", description="用户类型"),
        dept_id: Optional[str] = Query(None, alias="dept_ids", description="部门ID"),
        db: AsyncSession = Depends(get_db)
):
    """获取用户列表（分页）"""
    from core.user.model import User

    filters = []
    if name:
        filters.append(User.name.ilike(f"%{name}%"))
    if username:
        filters.append(User.username.ilike(f"%{username}%"))
    if mobile:
        filters.append(User.mobile.ilike(f"%{mobile}%"))
    if email:
        filters.append(User.email.ilike(f"%{email}%"))
    if user_status is not None:
        filters.append(User.user_status == user_status)
    if user_type is not None:
        filters.append(User.user_type == user_type)
    if dept_id:
        filters.append(User.dept_id == dept_id)

    items, total = await UserService.get_list(db, page=page, page_size=page_size, filters=filters)

    # 为每个用户添加 role_ids
    response_items = []
    for item in items:
        user_dict = _build_user_response(item).model_dump()
        # 获取用户的角色ID列表
        role_ids = await UserService.get_user_role_ids(db, item.id)
        user_dict['role_ids'] = role_ids
        response_items.append(user_dict)

    return PaginatedResponse(
        items=response_items,
        total=total
    )


@router.get("/simple", response_model=List[UserSimple], summary="获取用户简单列表")
async def get_user_simple_list(
        user_status: Optional[int] = Query(None, alias="userStatus", description="用户状态"),
        dept_id: Optional[str] = Query(None, alias="deptId", description="部门ID"),
        db: AsyncSession = Depends(get_db)
):
    """获取用户简单列表（用于选择器）"""
    from core.user.model import User

    filters = []
    if user_status is not None:
        filters.append(User.user_status == user_status)
    if dept_id:
        filters.append(User.dept_id == dept_id)

    items, _ = await UserService.get_list(db, page=1, page_size=1000, filters=filters)
    return [_build_user_simple(item) for item in items]


@router.get("/export/excel", summary="导出用户Excel")
async def export_user_excel(db: AsyncSession = Depends(get_db)):
    """导出用户到Excel"""
    output = await UserService.export_to_excel(db)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=users.xlsx"}
    )


@router.get("/import/template", summary="下载用户导入模板")
async def download_user_template():
    """下载用户导入模板"""
    output = UserService.get_import_template()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=user_template.xlsx"}
    )


@router.post("/import/excel", response_model=ResponseModel, summary="导入用户Excel")
async def import_user_excel(
        file: UploadFile = File(..., description="Excel文件(.xlsx)"),
        db: AsyncSession = Depends(get_db)
):
    """从Excel导入用户"""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="只支持.xlsx格式")

    content = await file.read()
    success, fail = await UserService.import_from_excel(db, content)
    return ResponseModel(message=f"成功{success}条，失败{fail}条", data={"success": success, "fail": fail})


@router.get("/check/unique", response_model=ResponseModel, summary="检查用户唯一性")
async def check_user_unique(
        field: str = Query(..., description="字段名"),
        value: str = Query(..., description="字段值"),
        exclude_id: Optional[str] = Query(None, alias="excludeId", description="排除ID"),
        db: AsyncSession = Depends(get_db)
):
    """检查用户字段唯一性"""
    allowed_fields = ["username", "email", "mobile"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段: {field}")

    is_unique = await UserService.check_unique(db, field=field, value=value, exclude_id=exclude_id)
    return ResponseModel(message="可用" if is_unique else "已存在", data={"unique": is_unique})


@router.post("/batch_delete", response_model=UserBatchDeleteOut, summary="批量删除用户")
async def batch_delete_users(
        data: UserBatchDeleteIn,
        db: AsyncSession = Depends(get_db)
):
    """批量删除用户"""
    success_count, fail_count = await UserService.batch_delete(db, data.ids)
    return UserBatchDeleteOut(success_count=success_count, fail_count=fail_count)


@router.post("/batch/status", response_model=UserBatchUpdateStatusOut, summary="批量更新用户状态")
async def batch_update_user_status(
        data: UserBatchUpdateStatusIn,
        db: AsyncSession = Depends(get_db)
):
    """批量更新用户状态"""
    count = await UserService.batch_update_status(db, data.ids, data.user_status)
    return UserBatchUpdateStatusOut(count=count)


@router.get("/org-chart/top", response_model=List[OrgChartNode], summary="获取组织架构顶层节点")
async def get_org_chart_top(
        db: AsyncSession = Depends(get_db)
):
    """获取组织架构顶层用户（无上级）"""
    users = await UserService.get_top_users(db)
    result = []
    for user in users:
        count = await UserService.get_subordinate_count(db, user.id)
        result.append(_build_org_chart_node(user, count))
    return result


@router.get("/org-chart/{user_id}", response_model=OrgChartNode, summary="获取指定用户的组织架构节点")
async def get_org_chart_node(
        user_id: str,
        db: AsyncSession = Depends(get_db)
):
    """获取指定用户的组织架构节点信息"""
    user = await UserService.get_by_id(db, record_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    count = await UserService.get_subordinate_count(db, user.id)
    return _build_org_chart_node(user, count)


@router.get("/org-chart/{user_id}/chain", response_model=OrgChartChainNode, summary="获取用户汇报链")
async def get_org_chart_chain(
        user_id: str,
        db: AsyncSession = Depends(get_db)
):
    """获取从指定用户到顶层的完整汇报链（嵌套树结构，顶层为根）"""
    chain = await UserService.get_report_chain(db, user_id)
    if not chain:
        raise HTTPException(status_code=404, detail="用户不存在")

    # chain: [当前用户, 上级, 上上级, ..., 顶层]
    # 从当前用户开始往上构建嵌套，每个上级把下级作为 children
    result = None
    for user in chain:
        count = await UserService.get_subordinate_count(db, user.id)
        node = _build_org_chart_node(user, count)
        chain_node = OrgChartChainNode(
            id=node.id,
            name=node.name,
            username=node.username,
            avatar=node.avatar,
            dept_name=node.dept_name,
            post_name=node.post_name,
            subordinate_count=node.subordinate_count,
            children=[result] if result else [],
        )
        result = chain_node

    return result


@router.get("/org-chart/{user_id}/children", response_model=List[OrgChartNode], summary="获取组织架构子节点")
async def get_org_chart_children(
        user_id: str,
        db: AsyncSession = Depends(get_db)
):
    """获取指定用户的下属（组织架构子节点）"""
    subordinates = await UserService.get_subordinates(db, user_id)
    result = []
    for user in subordinates:
        count = await UserService.get_subordinate_count(db, user.id)
        result.append(_build_org_chart_node(user, count))
    return result


@router.get("/{user_id}/subordinates", response_model=List[UserSimple], summary="获取下属用户")
async def get_user_subordinates(
        user_id: str,
        db: AsyncSession = Depends(get_db)
):
    """获取下属用户列表"""
    subordinates = await UserService.get_subordinates(db, user_id)
    return [_build_user_simple(item) for item in subordinates]


@router.post("/{user_id}/reset-password", response_model=ResponseModel, summary="重置用户密码")
async def reset_user_password(
        user_id: str,
        data: UserPasswordSetIn,
        db: AsyncSession = Depends(get_db)
):
    """管理员重置用户密码"""
    success = await UserService.reset_password(db, user_id, data.new_password)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel(message="密码重置成功")


@router.post("/change-password", response_model=ResponseModel, summary="当前用户修改密码")
async def change_my_password(
        data: UserPasswordResetIn,
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
):
    """当前登录用户修改自己的密码"""
    success, message = await UserService.change_password(
        db, user_id, data.old_password, data.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return ResponseModel(message=message)


@router.post("/{user_id}/change-password", response_model=ResponseModel, summary="管理员修改用户密码")
async def change_user_password(
        user_id: str,
        data: UserPasswordResetIn,
        db: AsyncSession = Depends(get_db)
):
    """管理员修改指定用户的密码"""
    success, message = await UserService.change_password(
        db, user_id, data.old_password, data.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return ResponseModel(message=message)


@router.get("/profile", response_model=UserResponse, summary="获取当前用户详细信息")
async def get_my_profile(
        current_user=Depends(get_current_user)
):
    """获取当前登录用户的详细信息"""
    return _build_user_response(current_user)


@router.put("/profile", response_model=UserResponse, summary="更新当前用户个人信息")
async def update_my_profile(
        data: UserProfileUpdateIn,
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
):
    """更新当前登录用户的个人信息"""
    # 邮箱唯一性校验
    if data.email:
        if not await UserService.check_unique(db, field="email", value=data.email, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="邮箱已存在")

    # 手机号唯一性校验
    if data.mobile:
        if not await UserService.check_unique(db, field="mobile", value=data.mobile, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="手机号已存在")

    # 转换为UserUpdate
    update_data = UserUpdate(**data.model_dump(exclude_unset=True))
    user = await UserService.update(db, record_id=user_id, data=update_data)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _build_user_response(user)


@router.put("/{user_id}/profile", response_model=UserResponse, summary="更新指定用户个人信息（管理员）")
async def update_user_profile(
        user_id: str,
        data: UserProfileUpdateIn,
        db: AsyncSession = Depends(get_db)
):
    """更新指定用户的个人信息（管理员功能）"""
    # 邮箱唯一性校验
    if data.email:
        if not await UserService.check_unique(db, field="email", value=data.email, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="邮箱已存在")

    # 手机号唯一性校验
    if data.mobile:
        if not await UserService.check_unique(db, field="mobile", value=data.mobile, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="手机号已存在")

    # 转换为UserUpdate
    update_data = UserUpdate(**data.model_dump(exclude_unset=True))
    user = await UserService.update(db, record_id=user_id, data=update_data)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _build_user_response(user)


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user_by_id(user_id: str, db: AsyncSession = Depends(get_db)):
    """获取用户详情"""
    user = await UserService.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 构建响应并添加 role_ids
    user_dict = _build_user_response(user).model_dump()
    role_ids = await UserService.get_user_role_ids(db, user_id)
    user_dict['role_ids'] = role_ids
    return user_dict


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    """更新用户"""
    # 用户名唯一性校验
    if data.username:
        if not await UserService.check_unique(db, field="username", value=data.username, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="用户名已存在")

    # 邮箱唯一性校验
    if data.email:
        if not await UserService.check_unique(db, field="email", value=data.email, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="邮箱已存在")

    # 手机号唯一性校验
    if data.mobile:
        if not await UserService.check_unique(db, field="mobile", value=data.mobile, exclude_id=user_id):
            raise HTTPException(status_code=400, detail="手机号已存在")

    user = await UserService.update(db, record_id=user_id, data=data)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 构建响应并添加 role_ids
    user_dict = _build_user_response(user).model_dump()
    role_ids = await UserService.get_user_role_ids(db, user_id)
    user_dict['role_ids'] = role_ids
    return user_dict


@router.delete("/{user_id}", response_model=ResponseModel, summary="删除用户")
async def delete_user(
        user_id: str,
        hard: bool = Query(default=False, description="是否物理删除"),
        db: AsyncSession = Depends(get_db)
):
    """删除用户"""
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user.can_delete():
        raise HTTPException(status_code=400, detail="系统用户或超级管理员不能删除")

    success = await UserService.delete(db, record_id=user_id, hard=hard)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseModel(message="删除成功")


def _build_user_response(user) -> UserResponse:
    """构建用户响应"""
    # 获取岗位名称
    post_name = None
    if hasattr(user, 'post') and user.post:
        post_name = user.post.name

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        mobile=user.mobile,
        avatar=user.avatar,
        name=user.name,
        gender=user.gender if user.gender is not None else 0,
        gender_display=user.get_gender_display(),
        user_type=user.user_type if user.user_type is not None else 1,
        user_type_display=user.get_user_type_display(),
        user_status=user.user_status if user.user_status is not None else 1,
        user_status_display=user.get_user_status_display(),
        birthday=user.birthday,
        city=user.city,
        address=user.address,
        bio=user.bio,
        is_superuser=user.is_superuser,
        is_active=user.is_active,
        dept_id=user.dept_id,
        post_id=user.post_id,
        post_name=post_name,
        manager_id=user.manager_id,
        last_login=user.last_login,
        last_login_ip=user.last_login_ip,
        last_login_type=user.last_login_type,
        sort=user.sort,
        is_deleted=user.is_deleted,
        sys_create_datetime=user.sys_create_datetime,
        sys_update_datetime=user.sys_update_datetime,
    )


def _build_org_chart_node(user, subordinate_count: int = 0) -> OrgChartNode:
    """构建组织架构节点"""
    post_name = None
    if hasattr(user, 'post') and user.post:
        post_name = user.post.name
    return OrgChartNode(
        id=user.id,
        name=user.name,
        username=user.username,
        avatar=user.avatar,
        dept_name=user.dept.name if user.dept else None,
        post_name=post_name,
        subordinate_count=subordinate_count,
    )


def _build_user_simple(user) -> UserSimple:
    """构建用户简单响应"""
    return UserSimple(
        id=user.id,
        name=user.name,
        username=user.username,
        avatar=user.avatar,
        email=user.email,
        mobile=user.mobile,
        dept_name=user.dept.name if user.dept else None,
    )
