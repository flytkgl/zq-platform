from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from utils.context import get_current_user_info_from_context
from utils.permission import apply_data_scope_filter


def get_data_scope_filter(request: Request):
    """
    FastAPI依赖函数：获取当前请求的数据权限过滤参数
    
    使用方式：
    @router.get("/users")
    async def get_users(
        data_scope = Depends(get_data_scope_filter),
        db: AsyncSession = Depends(get_db)
    ):
        items, total = await UserService.get_list_with_data_scope(
            db=db,
            **data_scope,  # 自动展开为 role_id, is_superuser, user_id, user_dept_id, request_path, http_method
            page=page,
            page_size=page_size
        )
    
    :param request: FastAPI Request对象
    :return: 数据权限参数字典
    """
    # 从上下文获取用户信息（由中间件设置）
    user_info = get_current_user_info_from_context()
    
    if not user_info:
        # 如果上下文中没有用户信息，返回默认值（不应该发生，因为有认证中间件）
        return {
            "role_id": None,
            "is_superuser": False,
            "user_id": None,
            "user_dept_id": None,
            "request_path": request.url.path,
            "http_method": request.method
        }
    
    return {
        "role_id": user_info.get("role_id"),
        "is_superuser": user_info.get("is_superuser", False),
        "user_id": user_info.get("user_id"),
        "user_dept_id": user_info.get("dept_id"),
        "request_path": request.url.path,
        "http_method": request.method
    }


async def get_data_scope_dict(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    FastAPI依赖函数：获取当前请求的数据权限过滤条件字典
    
    使用方式：
    @router.get("/users")
    async def get_users(
        data_scope_dict = Depends(get_data_scope_dict),
        db: AsyncSession = Depends(get_db)
    ):
        # data_scope_dict 包含 filter_type, user_id, dept_id, dept_ids 等
        if data_scope_dict['filter_type'] == 'self':
            query = query.where(User.id == data_scope_dict['user_id'])
        ...
    
    :param request: FastAPI Request对象
    :param db: 数据库会话
    :return: 数据权限过滤条件字典
    """
    # 从上下文获取用户信息（由中间件设置）
    user_info = get_current_user_info_from_context()
    
    if not user_info:
        # 如果上下文中没有用户信息，返回默认的全部数据权限
        return {
            'scope': 0,
            'filter_type': 'all',
            'user_id': None,
            'dept_id': None,
            'dept_ids': None,
        }
    
    return await apply_data_scope_filter(
        db=db,
        role_id=user_info.get("role_id"),
        is_superuser=user_info.get("is_superuser", False),
        user_id=user_info.get("user_id"),
        user_dept_id=user_info.get("dept_id"),
        request_path=request.url.path,
        http_method=request.method
    )


def get_current_user_id(current_user = Depends(get_current_user)) -> str:
    """
    FastAPI依赖函数：获取当前用户ID
    
    使用方式：
    @router.post("/posts")
    async def create_post(
        data: PostCreate,
        current_user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db)
    ):
        post = await PostService.create(db, data, current_user_id=current_user_id)
        return post
    
    :param current_user: 当前用户
    :return: 用户ID
    """
    return current_user.id
