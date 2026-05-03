"""
上下文管理器 - 用于在整个请求生命周期中共享数据
"""
from contextvars import ContextVar
from typing import Optional, Dict, Any

# 当前用户信息上下文
current_user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('current_user', default=None)


def get_current_user_id_from_context() -> Optional[str]:
    """
    从上下文中获取当前用户ID
    
    :return: 用户ID，如果未设置则返回None
    """
    user_info = current_user_context.get()
    return user_info.get('user_id') if user_info else None


def get_current_user_info_from_context() -> Optional[Dict[str, Any]]:
    """
    从上下文中获取当前用户完整信息
    
    :return: 用户信息字典，包含 user_id, role_id, dept_id, is_superuser 等
    """
    return current_user_context.get()


def set_current_user_context(
    user_id: str,
    role_id: Optional[str] = None,
    dept_id: Optional[str] = None,
    is_superuser: bool = False,
    username: Optional[str] = None,
    request_path: Optional[str] = None,
    http_method: Optional[str] = None,
    role_ids: Optional[list] = None
) -> None:
    """
    设置当前用户信息到上下文
    
    :param user_id: 用户ID
    :param role_id: 角色ID（单个，向后兼容）
    :param dept_id: 部门ID
    :param is_superuser: 是否超级管理员
    :param username: 用户名
    :param request_path: 请求路径
    :param http_method: HTTP方法
    :param role_ids: 角色ID列表（多个角色）
    """
    # 如果提供了 role_ids，使用它；否则从 role_id 构建
    if role_ids is None and role_id:
        role_ids = [role_id]
    elif role_ids is None:
        role_ids = []
    
    current_user_context.set({
        'user_id': user_id,
        'role_id': role_id,  # 保持向后兼容
        'role_ids': role_ids,  # 新增：支持多角色
        'dept_id': dept_id,
        'is_superuser': is_superuser,
        'username': username,
        'request_path': request_path,
        'http_method': http_method
    })


def clear_current_user_context() -> None:
    """清除当前用户上下文"""
    current_user_context.set(None)


# 保持向后兼容的别名
set_current_user_id_context = lambda user_id: set_current_user_context(user_id)
clear_current_user_id_context = clear_current_user_context
