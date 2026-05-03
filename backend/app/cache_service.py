"""
带缓存的通用服务基类
继承BaseService，添加Redis缓存支持
"""
from typing import TypeVar, Type, Optional, List, Tuple, Dict, Callable, Any, ClassVar

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.base_model import BaseModel as DBBaseModel
from app.base_service import BaseService
from utils.redis import CacheManager

T = TypeVar("T", bound=DBBaseModel)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class CacheService(BaseService[T, CreateSchema, UpdateSchema]):
    """
    带缓存的通用服务基类
    继承BaseService，添加Redis缓存支持
    
    子类需要定义：
    - model: 数据模型类
    - cache_prefix: 缓存key前缀
    - cache_expire: 缓存过期时间（秒）
    
    可选覆盖：
    - _serialize_for_cache: 自定义序列化方法
    """
    
    # 子类必须定义
    model: ClassVar[Type[DBBaseModel]]
    
    # 缓存配置，子类可覆盖
    cache_prefix: ClassVar[str] = ""
    cache_expire: ClassVar[int] = 300
    
    # 缓存key模板
    CACHE_KEY_DETAIL: ClassVar[str] = "detail:{id}"
    CACHE_KEY_LIST: ClassVar[str] = "list:page:{page}:size:{size}"
    
    # 缓存管理器（延迟初始化）
    _cache_manager: ClassVar[Optional[CacheManager]] = None
    
    @classmethod
    def _get_cache(cls) -> CacheManager:
        """获取缓存管理器（延迟初始化）"""
        if cls._cache_manager is None or cls._cache_manager.prefix != f"{cls.cache_prefix}":
            cls._cache_manager = CacheManager(prefix=cls.cache_prefix)
        return cls._cache_manager
    
    @classmethod
    def _serialize_for_cache(cls, item: Any) -> Dict[str, Any]:
        """
        将model对象序列化为可缓存的字典
        子类可覆盖此方法自定义序列化逻辑
        """
        return {
            "id": item.id,
            "sort": item.sort,
            "is_deleted": item.is_deleted,
            "sys_create_datetime": str(item.sys_create_datetime),
            "sys_update_datetime": str(item.sys_update_datetime),
        }
    
    @classmethod
    async def create(cls, db: AsyncSession, data: CreateSchema) -> Any:
        """创建记录并清除列表缓存"""
        result = await super().create(db, data)
        # 清除列表缓存
        await cls._get_cache().delete_pattern("list:*")
        return result
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, record_id: str) -> Optional[Any]:
        """
        根据ID获取记录（优先从缓存获取）
        """
        cache = cls._get_cache()
        cache_key = cls.CACHE_KEY_DETAIL.format(id=record_id)
        
        # 尝试从缓存获取
        cached = await cache.get(cache_key)
        if cached:
            return cached
        
        # 缓存未命中，从数据库获取
        result = await super().get_by_id(db, record_id)
        if result:
            # 序列化并写入缓存
            cache_data = cls._serialize_for_cache(result)
            await cache.set(cache_key, cache_data, cls.cache_expire)
        
        return result
    
    @classmethod
    async def get_by_id_no_cache(cls, db: AsyncSession, record_id: str) -> Optional[Any]:
        """根据ID获取记录（不使用缓存）"""
        return await super().get_by_id(db, record_id)
    
    @classmethod
    async def get_list(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Any]] = None
    ) -> Tuple[List[Any], int]:
        """
        获取列表（优先从缓存获取，仅缓存无过滤条件的查询）
        """
        # 有过滤条件时不使用缓存
        if filters:
            return await super().get_list(db, page, page_size, filters)
        
        cache = cls._get_cache()
        cache_key = cls.CACHE_KEY_LIST.format(page=page, size=page_size)
        
        # 尝试从缓存获取
        cached = await cache.get(cache_key)
        if cached:
            return cached.get("items", []), cached.get("total", 0)
        
        # 缓存未命中，从数据库获取
        items, total = await super().get_list(db, page, page_size, filters)
        
        # 序列化并写入缓存
        cache_data = {
            "items": [cls._serialize_for_cache(item) for item in items],
            "total": total
        }
        await cache.set(cache_key, cache_data, cls.cache_expire)
        
        return items, total
    
    @classmethod
    async def get_list_no_cache(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Any]] = None
    ) -> Tuple[List[Any], int]:
        """获取列表（不使用缓存）"""
        return await super().get_list(db, page, page_size, filters)
    
    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        record_id: str,
        data: UpdateSchema
    ) -> Optional[Any]:
        """更新记录并清除相关缓存"""
        result = await super().update(db, record_id, data)
        if result:
            cache = cls._get_cache()
            # 清除单条记录缓存
            await cache.delete(cls.CACHE_KEY_DETAIL.format(id=record_id))
            # 清除列表缓存
            await cache.delete_pattern("list:*")
        return result
    
    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        record_id: str,
        hard: bool = False
    ) -> bool:
        """删除记录并清除相关缓存"""
        result = await super().delete(db, record_id, hard)
        if result:
            cache = cls._get_cache()
            # 清除单条记录缓存
            await cache.delete(cls.CACHE_KEY_DETAIL.format(id=record_id))
            # 清除列表缓存
            await cache.delete_pattern("list:*")
        return result
    
    @classmethod
    async def clear_cache(cls, record_id: Optional[str] = None) -> int:
        """
        手动清除缓存
        
        :param record_id: 指定ID则只清除该记录缓存，否则清除所有缓存
        :return: 清除的key数量
        """
        cache = cls._get_cache()
        if record_id:
            return await cache.delete(cls.CACHE_KEY_DETAIL.format(id=record_id))
        else:
            return await cache.delete_pattern("*")
    
    @classmethod
    async def refresh_cache(cls, db: AsyncSession, record_id: str) -> bool:
        """
        刷新指定记录的缓存
        
        :param record_id: 记录ID
        :return: 是否成功
        """
        # 先删除缓存
        await cls._get_cache().delete(cls.CACHE_KEY_DETAIL.format(id=record_id))
        # 重新获取（会自动写入缓存）
        result = await cls.get_by_id(db, record_id)
        return result is not None
    
    @classmethod
    async def get_cache_stats(cls, record_id: str) -> Dict[str, Any]:
        """
        获取缓存状态信息
        
        :param record_id: 记录ID
        :return: 缓存状态信息
        """
        cache = cls._get_cache()
        cache_key = cls.CACHE_KEY_DETAIL.format(id=record_id)
        exists = await cache.exists(cache_key)
        ttl = await cache.ttl(cache_key) if exists else -2
        
        return {
            "key": f"{cache.prefix}{cache_key}",
            "exists": exists,
            "ttl": ttl
        }
    
    @classmethod
    async def import_from_excel(
        cls,
        db: AsyncSession,
        file_content: bytes,
        row_processor: Optional[Callable[[Dict[str, Any]], Optional[Any]]] = None
    ) -> Tuple[int, int]:
        """从Excel导入数据并清除列表缓存"""
        result = await super().import_from_excel(db, file_content, row_processor)
        # 清除列表缓存
        await cls._get_cache().delete_pattern("list:*")
        return result
