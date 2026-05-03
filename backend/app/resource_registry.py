#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资源类型注册表 - 自动注册和管理所有资源类型
"""
import re
from typing import Dict, List, Type, Optional


class ResourceRegistry:
    """
    资源类型注册表
    
    自动注册所有定义了 RESOURCE_TYPE 的 Service，
    并提供查询、验证等功能
    """
    
    # 存储所有已注册的资源类型
    # 格式: {resource_type: {"service": ServiceClass, "model": ModelClass, "name": "显示名称"}}
    _registry: Dict[str, Dict] = {}
    
    @classmethod
    def register(
        cls,
        resource_type: str,
        service_class: Type,
        display_name: Optional[str] = None,
        application_id: Optional[str] = None,
        field_metadata: Optional[Dict[str, Dict]] = None
    ):
        """
        注册资源类型
        
        :param resource_type: 资源类型标识（如 'customer', 'order'）
        :param service_class: Service 类
        :param display_name: 显示名称（可选，如 '客户', '订单'）
        :param application_id: 应用ID（可选，用于子应用过滤）
        :param field_metadata: 字段元数据（可选，用于字段权限配置）
        """
        if resource_type in cls._registry:
            # 如果已存在，更新信息
            cls._registry[resource_type].update({
                'service': service_class,
                'display_name': display_name or cls._registry[resource_type].get('display_name', resource_type),
                'application_id': application_id or cls._registry[resource_type].get('application_id'),
                'field_metadata': field_metadata or cls._registry[resource_type].get('field_metadata')
            })
        else:
            # 新注册
            cls._registry[resource_type] = {
                'service': service_class,
                'model': service_class.model if service_class and hasattr(service_class, 'model') else None,
                'display_name': display_name or cls._generate_display_name(resource_type),
                'application_id': application_id,
                'field_metadata': field_metadata
            }
    
    @classmethod
    def _generate_display_name(cls, resource_type: str) -> str:
        """
        根据资源类型生成显示名称
        
        :param resource_type: 资源类型（如 'customer_order'）
        :return: 显示名称（如 '客户订单'）
        """
        # 将下划线分隔的单词转换为空格分隔，并首字母大写
        words = resource_type.split('_')
        return ' '.join(word.capitalize() for word in words)
    
    @classmethod
    def get_all_resource_types(cls) -> List[str]:
        """
        获取所有已注册的资源类型
        
        :return: 资源类型列表
        """
        return list(cls._registry.keys())
    
    @classmethod
    def get_all_resources(cls, application_id: Optional[str] = None) -> List[Dict]:
        """
        获取所有已注册的资源信息
        
        :param application_id: 应用ID，如果指定则只返回该应用的资源（严格匹配）
        :return: 资源信息列表，每个元素包含 resource_type, display_name, model_name 等
        """
        resources = []
        for resource_type, info in cls._registry.items():
            # 如果指定了应用ID，只返回该应用的资源（严格匹配，不显示无应用ID的资源）
            if application_id:
                resource_app_id = info.get('application_id')
                # 只显示匹配该应用ID的资源
                if resource_app_id != application_id:
                    continue
            
            resources.append({
                'resource_type': resource_type,
                'display_name': info.get('display_name', resource_type),
                'model_name': info['model'].__name__ if info.get('model') else None,
                'table_name': info['model'].__tablename__ if info.get('model') and hasattr(info['model'], '__tablename__') else None,
                'application_id': info.get('application_id')
            })
        return resources
    
    @classmethod
    def get_resource(cls, resource_type: str) -> Optional[Dict]:
        """
        根据资源类型获取完整的资源信息
        
        :param resource_type: 资源类型
        :return: 资源信息字典或 None
        """
        return cls._registry.get(resource_type)
    
    @classmethod
    def get_service(cls, resource_type: str) -> Optional[Type]:
        """
        根据资源类型获取对应的 Service 类
        
        :param resource_type: 资源类型
        :return: Service 类或 None
        """
        info = cls._registry.get(resource_type)
        return info.get('service') if info else None
    
    @classmethod
    def validate_resource_type(cls, resource_type: str) -> bool:
        """
        验证资源类型是否已注册（别名方法）
        
        :param resource_type: 资源类型
        :return: True 表示已注册，False 表示未注册
        """
        return resource_type in cls._registry
    
    @classmethod
    def validate(cls, resource_type: str) -> bool:
        """
        验证资源类型是否已注册
        
        :param resource_type: 资源类型
        :return: True 表示已注册，False 表示未注册
        """
        return resource_type in cls._registry
    
    @classmethod
    def unregister(cls, resource_type: str) -> bool:
        """
        注销资源类型
        
        :param resource_type: 资源类型标识
        :return: True 表示成功注销，False 表示资源类型不存在
        """
        if resource_type in cls._registry:
            del cls._registry[resource_type]
            return True
        return False
    
    @classmethod
    def clear(cls):
        """清空注册表（主要用于测试）"""
        cls._registry.clear()
    
    @classmethod
    def get_registry_info(cls) -> Dict:
        """
        获取注册表的统计信息
        
        :return: 统计信息字典
        """
        return {
            'total_count': len(cls._registry),
            'resource_types': cls.get_all_resource_types(),
            'resources': cls.get_all_resources()
        }


def auto_generate_resource_type(model_class: Type) -> str:
    """
    根据模型类自动生成资源类型
    
    规则：
    1. 优先使用表名（去除前缀如 core_, sys_）
    2. 如果没有表名，使用模型名（驼峰转下划线）
    
    :param model_class: 模型类
    :return: 资源类型字符串
    """
    # 尝试从表名生成
    if hasattr(model_class, '__tablename__'):
        table_name = model_class.__tablename__
        
        # 移除常见前缀
        for prefix in ['core_', 'sys_', 'app_', 'biz_']:
            if table_name.startswith(prefix):
                return table_name[len(prefix):]
        
        return table_name
    
    # 从模型名生成（驼峰转下划线）
    model_name = model_class.__name__
    # Customer → customer, CustomerOrder → customer_order
    resource_type = re.sub(r'(?<!^)(?=[A-Z])', '_', model_name).lower()
    
    return resource_type
