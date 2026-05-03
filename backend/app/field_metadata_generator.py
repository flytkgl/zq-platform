"""
字段元数据自动生成工具
从 SQLAlchemy Model 或 Pydantic Schema 自动生成 FIELD_METADATA
"""
from typing import Dict, Any, Type, get_origin, get_args, Union
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeMeta
from pydantic import BaseModel
import inspect as py_inspect


def generate_field_metadata(
    model: Type[DeclarativeMeta],
    sensitive_fields: list = None,
    maskable_fields: list = None,
    hidden_fields: list = None,
    field_labels: Dict[str, str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    从 SQLAlchemy Model 自动生成字段元数据
    
    Args:
        model: SQLAlchemy Model 类
        sensitive_fields: 敏感字段列表，如 ['mobile', 'email']
        maskable_fields: 可脱敏字段列表，如 ['mobile', 'email', 'id_card']
        hidden_fields: 默认隐藏字段列表，如 ['password']
        field_labels: 字段中文名称映射，如 {'name': '姓名', 'mobile': '手机号'}
    
    Returns:
        字段元数据字典
    
    Example:
        >>> FIELD_METADATA = generate_field_metadata(
        ...     User,
        ...     sensitive_fields=['mobile', 'email', 'password'],
        ...     maskable_fields=['mobile', 'email'],
        ...     hidden_fields=['password'],
        ...     field_labels={'name': '姓名', 'mobile': '手机号'}
        ... )
    """
    sensitive_fields = sensitive_fields or []
    maskable_fields = maskable_fields or []
    hidden_fields = hidden_fields or []
    field_labels = field_labels or {}
    
    metadata = {}
    
    # 获取 Model 的所有列
    mapper = inspect(model)
    
    for column in mapper.columns:
        field_name = column.name
        
        # 跳过内部字段
        if field_name.startswith('_'):
            continue
        
        # 确定字段类型
        field_type = _get_field_type(column.type)
        
        # 确定默认权限
        default_permission = "hidden" if field_name in hidden_fields else "read"
        
        # 生成字段标签
        label = field_labels.get(field_name) or _generate_label(field_name, column.comment)
        
        metadata[field_name] = {
            "label": label,
            "field_type": field_type,
            "sensitive": field_name in sensitive_fields,
            "maskable": field_name in maskable_fields,
            "default_permission": default_permission
        }
    
    return metadata


def _get_field_type(column_type) -> str:
    """
    根据 SQLAlchemy 列类型确定字段类型
    
    Args:
        column_type: SQLAlchemy 列类型
    
    Returns:
        字段类型字符串: string/integer/boolean/datetime/float
    """
    type_name = column_type.__class__.__name__.lower()
    
    if 'int' in type_name or 'serial' in type_name:
        return "integer"
    elif 'bool' in type_name:
        return "boolean"
    elif 'date' in type_name or 'time' in type_name:
        return "datetime"
    elif 'float' in type_name or 'numeric' in type_name or 'decimal' in type_name:
        return "float"
    else:
        return "string"


def _generate_label(field_name: str, comment: str = None) -> str:
    """
    生成字段标签
    
    优先使用数据库注释，如果没有则根据字段名生成
    
    Args:
        field_name: 字段名
        comment: 数据库注释
    
    Returns:
        字段标签
    """
    if comment:
        return comment
    
    # 常见字段名映射
    common_labels = {
        'id': 'ID',
        'name': '名称',
        'code': '编码',
        'title': '标题',
        'description': '描述',
        'remark': '备注',
        'status': '状态',
        'sort': '排序',
        'create_time': '创建时间',
        'update_time': '更新时间',
        'created_at': '创建时间',
        'updated_at': '更新时间',
        'is_deleted': '是否删除',
        'is_active': '是否激活',
        'username': '用户名',
        'password': '密码',
        'email': '邮箱',
        'mobile': '手机号',
        'phone': '电话',
        'address': '地址',
        'avatar': '头像',
        'gender': '性别',
        'age': '年龄',
        'dept_id': '部门ID',
        'user_id': '用户ID',
        'role_id': '角色ID',
    }
    
    # 如果在常见映射中，直接返回
    if field_name in common_labels:
        return common_labels[field_name]
    
    # 处理带前缀的字段
    if field_name.startswith('sys_'):
        base_name = field_name[4:]
        if base_name in common_labels:
            return f"系统{common_labels[base_name]}"
    
    # 处理下划线分隔的字段名
    if '_' in field_name:
        parts = field_name.split('_')
        # 尝试翻译每个部分
        translated_parts = [common_labels.get(part, part.title()) for part in parts]
        return ''.join(translated_parts)
    
    # 默认返回首字母大写的字段名
    return field_name.replace('_', ' ').title()


def generate_field_metadata_from_schema(
    schema: Type[BaseModel],
    model: Type[DeclarativeMeta] = None
) -> Dict[str, Dict[str, Any]]:
    """
    从 Pydantic Response Schema 生成字段元数据
    
    优势：
    1. 根据 Schema 的 Optional 类型判断字段是否必填
    2. 必填字段标记为 required=True，前端禁止隐藏
    3. 可选字段可以被隐藏
    
    Args:
        schema: Pydantic Response Schema 类
        model: SQLAlchemy Model 类（可选，用于获取数据库注释）
    
    Returns:
        字段元数据字典
    """
    metadata = {}
    
    # 获取 Schema 的所有字段
    schema_fields = schema.model_fields
    
    # 如果提供了 model，获取数据库注释
    db_comments = {}
    if model:
        mapper = inspect(model)
        for column in mapper.columns:
            if column.comment:
                db_comments[column.name] = column.comment
    
    # 自动识别敏感/可脱敏字段的关键词
    sensitive_keywords = ['password', 'passwd', 'pwd', 'secret', 'token', 'key']
    maskable_keywords = ['mobile', 'phone', 'tel', 'email', 'mail', 'id_card', 'idcard', 'name']
    hidden_keywords = ['password', 'passwd', 'pwd', 'secret', 'token', 'key']
    
    for field_name, field_info in schema_fields.items():
        # 判断字段是否必填（非 Optional）
        is_required = field_info.is_required()
        
        # 获取字段类型
        field_type = _get_pydantic_field_type(field_info.annotation)
        
        # 生成标签
        label = db_comments.get(field_name) or _generate_label(field_name)
        
        # 判断是否敏感/可脱敏
        field_name_lower = field_name.lower()
        is_sensitive = any(keyword in field_name_lower for keyword in sensitive_keywords)
        is_maskable = any(keyword in field_name_lower for keyword in maskable_keywords)
        is_hidden = any(keyword in field_name_lower for keyword in hidden_keywords)
        
        # 默认权限
        default_permission = "hidden" if is_hidden else "read"
        
        metadata[field_name] = {
            "label": label,
            "field_type": field_type,
            "required": is_required,  # 必填字段，前端禁止隐藏
            "sensitive": is_sensitive,
            "maskable": is_maskable,
            "default_permission": default_permission
        }
    
    return metadata


def _get_pydantic_field_type(annotation) -> str:
    """
    从 Pydantic 字段类型获取字段类型字符串
    
    Args:
        annotation: Pydantic 字段类型注解
    
    Returns:
        字段类型字符串
    """
    # 处理 Optional 类型
    origin = get_origin(annotation)
    if origin is Union:
        args = get_args(annotation)
        # Optional[X] 实际是 Union[X, None]，取第一个非 None 类型
        annotation = next((arg for arg in args if arg is not type(None)), str)
    
    # 获取类型名称
    if hasattr(annotation, '__name__'):
        type_name = annotation.__name__.lower()
    else:
        type_name = str(annotation).lower()
    
    if 'int' in type_name:
        return "integer"
    elif 'bool' in type_name:
        return "boolean"
    elif 'datetime' in type_name or 'date' in type_name:
        return "datetime"
    elif 'float' in type_name or 'decimal' in type_name:
        return "float"
    else:
        return "string"


def auto_generate_field_metadata(model: Type[DeclarativeMeta]) -> Dict[str, Dict[str, Any]]:
    """
    完全自动生成字段元数据（使用默认规则）
    
    自动识别敏感字段：
    - password, passwd, pwd: 密码相关
    - mobile, phone, tel: 手机号相关
    - email, mail: 邮箱相关
    - id_card, idcard, identity: 身份证相关
    - bank_card, bankcard: 银行卡相关
    - secret, token, key: 密钥相关
    
    Args:
        model: SQLAlchemy Model 类
    
    Returns:
        字段元数据字典
    """
    # 自动识别敏感字段
    sensitive_keywords = [
        'password', 'passwd', 'pwd',
        'mobile', 'phone', 'tel',
        'email', 'mail',
        'id_card', 'idcard', 'identity',
        'bank_card', 'bankcard',
        'secret', 'token', 'key'
    ]
    
    # 自动识别可脱敏字段
    maskable_keywords = [
        'mobile', 'phone', 'tel',
        'email', 'mail',
        'id_card', 'idcard', 'identity',
        'name',  # 姓名可脱敏
    ]
    
    # 自动识别隐藏字段
    hidden_keywords = [
        'password', 'passwd', 'pwd',
        'secret', 'token', 'key'
    ]
    
    mapper = inspect(model)
    
    sensitive_fields = []
    maskable_fields = []
    hidden_fields = []
    
    for column in mapper.columns:
        field_name = column.name.lower()
        
        # 检查是否为敏感字段
        if any(keyword in field_name for keyword in sensitive_keywords):
            sensitive_fields.append(column.name)
        
        # 检查是否可脱敏
        if any(keyword in field_name for keyword in maskable_keywords):
            maskable_fields.append(column.name)
        
        # 检查是否默认隐藏
        if any(keyword in field_name for keyword in hidden_keywords):
            hidden_fields.append(column.name)
    
    return generate_field_metadata(
        model,
        sensitive_fields=sensitive_fields,
        maskable_fields=maskable_fields,
        hidden_fields=hidden_fields
    )
