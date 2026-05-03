from io import BytesIO
from typing import TypeVar, Generic, Type, Optional, List, Tuple, Dict, Callable, Any, ClassVar

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.base_model import BaseModel as DBBaseModel
from app.data_scope_utils import get_data_scope_filter, apply_data_scope_to_conditions
from utils.excel import ExcelHandler
from utils.context import get_current_user_id_from_context, get_current_user_info_from_context

T = TypeVar("T", bound=DBBaseModel)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class BaseService(Generic[T, CreateSchema, UpdateSchema]):
    """
    通用服务基类
    提供增删改查和Excel导入导出的通用实现
    
    资源类型自动生成规则：
    1. 如果子类定义了 RESOURCE_TYPE，直接使用
    2. 如果没有定义，根据 model.__tablename__ 自动生成（去除 core_/sys_ 等前缀）
    3. 如果没有表名，根据 model.__name__ 自动生成（驼峰转下划线）
    """
    
    # 子类必须定义
    model: ClassVar[Type[DBBaseModel]]
    
    # 资源类型（用于资源类型绑定的数据权限），子类可定义，不定义则自动生成
    RESOURCE_TYPE: ClassVar[Optional[str]] = None
    
    # 资源显示名称（可选，用于前端显示）
    RESOURCE_DISPLAY_NAME: ClassVar[Optional[str]] = None
    
    # Excel导入导出列映射，子类可覆盖
    excel_columns: ClassVar[Dict[str, str]]
    excel_sheet_name: ClassVar[str]
    
    # 字段元数据（用于列权限），子类可定义
    FIELD_METADATA: ClassVar[Dict[str, Dict[str, Any]]] = {}
    
    def __init_subclass__(cls, **kwargs):
        """
        子类初始化时自动注册资源类型和生成字段元数据
        """
        super().__init_subclass__(**kwargs)
        
        # 只处理具体的 Service 子类（有 model 属性的）
        if hasattr(cls, 'model') and cls.model is not None:
            # 如果没有定义 RESOURCE_TYPE，自动生成
            if cls.RESOURCE_TYPE is None:
                from app.resource_registry import auto_generate_resource_type
                cls.RESOURCE_TYPE = auto_generate_resource_type(cls.model)
            
            # 如果没有定义 FIELD_METADATA 或为空，自动生成
            if not cls.FIELD_METADATA or len(cls.FIELD_METADATA) == 0:
                from app.field_metadata_generator import auto_generate_field_metadata
                cls.FIELD_METADATA = auto_generate_field_metadata(cls.model)
            
            # 注册到资源注册表
            if cls.RESOURCE_TYPE:
                from app.resource_registry import ResourceRegistry
                ResourceRegistry.register(
                    resource_type=cls.RESOURCE_TYPE,
                    service_class=cls,
                    display_name=cls.RESOURCE_DISPLAY_NAME
                )
    
    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        data: CreateSchema,
        auto_commit: bool = True,
        current_user_id: Optional[str] = None
    ) -> Any:
        """
        创建记录
        
        :param db: 数据库会话
        :param data: 创建数据Schema
        :param auto_commit: 是否自动提交，默认True。在事务中使用时设为False
        :param current_user_id: 当前用户ID（可选），如果不传则自动从上下文获取
        :return: 创建的记录
        """
        db_obj = cls.model(**data.model_dump())
        
        # 从上下文获取用户信息
        user_info = get_current_user_info_from_context()
        
        # 自动设置创建人ID
        # 优先使用传入的 current_user_id，如果没有则从上下文获取
        user_id = current_user_id or (user_info.get('user_id') if user_info else None)
        if user_id and hasattr(db_obj, 'sys_creator_id'):
            db_obj.sys_creator_id = user_id
        
        # 自动设置部门ID
        if user_info and hasattr(db_obj, 'sys_dept_id'):
            dept_id = user_info.get('dept_id')
            if dept_id:
                db_obj.sys_dept_id = dept_id
        
        db.add(db_obj)
        if auto_commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
            await db.refresh(db_obj)
        return db_obj
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, record_id: str) -> Optional[Any]:
        """
        根据ID获取单条记录（排除已删除）
        
        :param db: 数据库会话
        :param record_id: 记录ID
        :return: 记录或None
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.id == record_id,
                cls.model.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_list(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Any]] = None
    ) -> Tuple[List[Any], int]:
        """
        获取列表（分页，排除已删除）
        
        :param db: 数据库会话
        :param page: 页码
        :param page_size: 每页数量
        :param filters: 额外的过滤条件列表
        :return: (数据列表, 总数)
        """
        base_query = select(cls.model).where(cls.model.is_deleted == False)  # noqa: E712
        
        # 添加额外过滤条件
        if filters:
            for f in filters:
                base_query = base_query.where(f)
        
        # 获取总数
        count_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 计算offset
        offset = (page - 1) * page_size
        
        # 获取分页数据
        result = await db.execute(
            base_query.order_by(
                desc(cls.model.sort),
                desc(cls.model.sys_create_datetime)
            )
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        return items, total
    
    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        record_id: str,
        data: UpdateSchema,
        auto_commit: bool = True,
        current_user_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        更新记录
        
        :param db: 数据库会话
        :param record_id: 记录ID
        :param data: 更新数据Schema
        :param auto_commit: 是否自动提交，默认True。在事务中使用时设为False
        :param current_user_id: 当前用户ID（可选），如果不传则自动从上下文获取
        :return: 更新后的记录或None
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # 自动设置修改人ID
        # 优先使用传入的 current_user_id，如果没有则从上下文获取
        user_id = current_user_id or get_current_user_id_from_context()
        if user_id and hasattr(db_obj, 'sys_modifier_id'):
            db_obj.sys_modifier_id = user_id
        
        if auto_commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
            await db.refresh(db_obj)
        return db_obj
    
    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        record_id: str,
        hard: bool = True,
        auto_commit: bool = True
    ) -> bool:
        """
        删除记录
        
        :param db: 数据库会话
        :param record_id: 记录ID
        :param hard: True为物理删除，False为逻辑删除
        :param auto_commit: 是否自动提交，默认True。在事务中使用时设为False
        :return: 是否删除成功
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            return False
        
        if hard:
            await db.delete(db_obj)
        else:
            db_obj.is_deleted = True
        if auto_commit:
            await db.commit()
        else:
            await db.flush()
        return True
    
    @classmethod
    async def batch_delete(
        cls,
        db: AsyncSession,
        ids: List[str],
        hard: bool = False,
        auto_commit: bool = True
    ) -> Tuple[int, int]:
        """
        批量删除记录
        
        :param db: 数据库会话
        :param ids: 记录ID列表
        :param hard: True为物理删除，False为逻辑删除
        :param auto_commit: 是否自动提交，默认True。在事务中使用时设为False
        :return: (成功数, 失败数)
        """
        success_count = 0
        fail_count = 0
        
        for record_id in ids:
            db_obj = await cls.get_by_id(db, record_id)
            if db_obj:
                if hard:
                    await db.delete(db_obj)
                else:
                    db_obj.is_deleted = True
                success_count += 1
            else:
                fail_count += 1
        
        if success_count > 0:
            if auto_commit:
                await db.commit()
            else:
                await db.flush()
        
        return success_count, fail_count
    
    @classmethod
    async def update_with_data_scope(
        cls,
        db: AsyncSession,
        record_id: str,
        data: UpdateSchema,
        auto_commit: bool = True,
        current_user_id: Optional[str] = None,
        dept_field: str = "sys_dept_id",
        user_field: str = "sys_creator_id"
    ) -> Optional[Any]:
        """
        更新记录（带数据权限检查）
        
        自动从上下文获取当前用户信息和请求信息，检查是否有权限修改此记录
        
        :param db: 数据库会话
        :param record_id: 记录ID
        :param data: 更新数据Schema
        :param auto_commit: 是否自动提交
        :param current_user_id: 当前用户ID（可选）
        :param dept_field: 部门字段名
        :param user_field: 用户字段名
        :return: 更新后的记录或None（记录不存在或无权限）
        """
        # 从上下文获取用户信息和请求信息
        user_info = get_current_user_info_from_context()
        if not user_info:
            return None
        
        # 获取数据权限过滤条件（优先使用资源类型绑定）
        data_scope_filter = await cls._get_data_scope_filter(db, user_info)
        
        # 构建查询，应用数据权限过滤
        query = select(cls.model).where(
            cls.model.id == record_id,
            cls.model.is_deleted == False  # noqa: E712
        )
        
        # 应用数据权限过滤
        query = cls._apply_data_scope_to_query(
            query=query,
            data_scope_filter=data_scope_filter,
            dept_field=dept_field,
            user_field=user_field
        )
        
        # 查询记录
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        # 如果没有找到记录，说明记录不存在或无权限
        if not db_obj:
            return None
        
        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # 自动设置修改人ID
        user_id = current_user_id or user_info.get("user_id")
        if user_id and hasattr(db_obj, 'sys_modifier_id'):
            db_obj.sys_modifier_id = user_id
        
        if auto_commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
            await db.refresh(db_obj)
        
        return db_obj
    
    @classmethod
    async def delete_with_data_scope(
        cls,
        db: AsyncSession,
        record_id: str,
        hard: bool = False,
        auto_commit: bool = True,
        dept_field: str = "sys_dept_id",
        user_field: str = "sys_creator_id"
    ) -> bool:
        """
        删除记录（带数据权限检查）
        
        自动从上下文获取当前用户信息和请求信息，检查是否有权限删除此记录
        
        :param db: 数据库会话
        :param record_id: 记录ID
        :param hard: True为物理删除，False为逻辑删除
        :param auto_commit: 是否自动提交
        :param dept_field: 部门字段名
        :param user_field: 用户字段名
        :return: 是否删除成功（False表示记录不存在或无权限）
        """
        # 从上下文获取用户信息和请求信息
        user_info = get_current_user_info_from_context()
        if not user_info:
            return False
        
        # 获取数据权限过滤条件（优先使用资源类型绑定）
        data_scope_filter = await cls._get_data_scope_filter(db, user_info)
        
        # 构建查询，应用数据权限过滤
        query = select(cls.model).where(
            cls.model.id == record_id,
            cls.model.is_deleted == False  # noqa: E712
        )
        
        # 应用数据权限过滤
        query = cls._apply_data_scope_to_query(
            query=query,
            data_scope_filter=data_scope_filter,
            dept_field=dept_field,
            user_field=user_field
        )
        
        # 查询记录
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        # 如果没有找到记录，说明记录不存在或无权限
        if not db_obj:
            return False
        
        # 执行删除
        if hard:
            await db.delete(db_obj)
        else:
            db_obj.is_deleted = True
        
        if auto_commit:
            await db.commit()
        else:
            await db.flush()
        
        return True
    
    @classmethod
    async def export_to_excel(
        cls,
        db: AsyncSession,
        data_converter: Optional[Callable[[Any], Dict[str, Any]]] = None
    ) -> BytesIO:
        """
        导出数据到Excel
        
        :param db: 数据库会话
        :param data_converter: 数据转换函数，将model转为dict，子类可自定义
        :return: Excel文件的BytesIO对象
        """
        result = await db.execute(
            select(cls.model).where(cls.model.is_deleted == False)  # noqa: E712
            .order_by(desc(cls.model.sort), desc(cls.model.sys_create_datetime))
        )
        items = result.scalars().all()
        
        # 转换数据
        if data_converter:
            data = [data_converter(item) for item in items]
        else:
            # 默认转换：使用excel_columns中的字段
            data = [
                {field: getattr(item, field, "") for field in cls.excel_columns.keys()}
                for item in items
            ]
        
        return ExcelHandler.export_to_excel(data, cls.excel_columns, cls.excel_sheet_name)
    
    @classmethod
    async def import_from_excel(
        cls,
        db: AsyncSession,
        file_content: bytes,
        row_processor: Optional[Callable[[Dict[str, Any]], Optional[Any]]] = None
    ) -> Tuple[int, int]:
        """
        从Excel导入数据
        
        :param db: 数据库会话
        :param file_content: Excel文件内容
        :param row_processor: 行数据处理函数，将dict转为model实例，子类可自定义
        :return: (成功数, 失败数)
        """
        rows = ExcelHandler.import_from_excel(file_content, cls.excel_columns)
        
        success_count = 0
        fail_count = 0
        
        for row in rows:
            try:
                if row_processor:
                    db_obj = row_processor(row)
                else:
                    # 默认处理：直接创建model实例
                    db_obj = cls.model(**row)
                
                if db_obj:
                    db.add(db_obj)
                    success_count += 1
            except Exception:
                fail_count += 1
        
        if success_count > 0:
            await db.commit()
        
        return success_count, fail_count
    
    @classmethod
    def get_import_template(cls) -> BytesIO:
        """获取导入模板"""
        return ExcelHandler.generate_template(cls.excel_columns, cls.excel_sheet_name)
    
    @classmethod
    async def check_unique(
        cls,
        db: AsyncSession,
        field: str,
        value: Any,
        exclude_id: Optional[str] = None
    ) -> bool:
        """
        检查字段值是否唯一
        
        :param db: 数据库会话
        :param field: 字段名
        :param value: 字段值
        :param exclude_id: 排除的记录ID（用于更新时排除自身）
        :return: True表示唯一，False表示已存在
        """
        query = select(cls.model).where(
            getattr(cls.model, field) == value,
            cls.model.is_deleted == False  # noqa: E712
        )
        
        # 更新时排除自身
        if exclude_id:
            query = query.where(cls.model.id != exclude_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is None
    
    @classmethod
    async def get_by_field(
        cls,
        db: AsyncSession,
        field: str,
        value: Any
    ) -> Optional[Any]:
        """
        根据字段获取单条记录
        
        :param db: 数据库会话
        :param field: 字段名
        :param value: 字段值
        :return: 记录或None
        """
        result = await db.execute(
            select(cls.model).where(
                getattr(cls.model, field) == value,
                cls.model.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def exists(
        cls,
        db: AsyncSession,
        filters: List[Any]
    ) -> bool:
        """
        检查是否存在符合条件的记录
        
        :param db: 数据库会话
        :param filters: 过滤条件列表
        :return: True表示存在，False表示不存在
        """
        query = select(cls.model).where(cls.model.is_deleted == False)  # noqa: E712
        for f in filters:
            query = query.where(f)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    @classmethod
    async def get_list_with_data_scope(
        cls,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Any]] = None,
        dept_field: str = "sys_dept_id",
        user_field: str = "sys_creator_id"
    ) -> Tuple[List[Any], int]:
        """
        获取列表（分页，带数据权限过滤）
        
        自动从上下文获取当前用户信息和请求信息，无需手动传递任何参数
        
        数据权限优先级：
        1. 优先使用资源类型绑定的数据权限（ResourceDataScopeConfig）
        2. 如果没有配置，回退到 API 绑定的数据权限（Permission.data_scope）
        3. 如果都没有，默认全部数据
        
        :param db: 数据库会话
        :param page: 页码
        :param page_size: 每页数量
        :param filters: 额外的过滤条件列表
        :param dept_field: 部门字段名（默认sys_dept_id）
        :param user_field: 用户字段名（默认sys_creator_id）
        :return: (数据列表, 总数)
        """
        # 从上下文获取用户信息和请求信息
        user_info = get_current_user_info_from_context()
        if not user_info:
            # 如果没有用户信息，返回空列表（不应该发生）
            return [], 0
        
        # 获取数据权限过滤条件
        data_scope_filter = await cls._get_data_scope_filter(db, user_info)
        
        # 构建基础查询
        base_query = select(cls.model).where(cls.model.is_deleted == False)  # noqa: E712
        
        # 添加业务过滤条件
        if filters:
            for f in filters:
                base_query = base_query.where(f)
        
        # 应用数据权限过滤
        base_query = cls._apply_data_scope_to_query(
            query=base_query,
            data_scope_filter=data_scope_filter,
            dept_field=dept_field,
            user_field=user_field
        )
        
        # 获取总数
        count_result = await db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0
        
        # 计算offset
        offset = (page - 1) * page_size
        
        # 获取分页数据
        result = await db.execute(
            base_query.order_by(
                desc(cls.model.sort),
                desc(cls.model.sys_create_datetime)
            )
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        return items, total
    
    @classmethod
    async def _get_data_scope_filter(
        cls,
        db: AsyncSession,
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取数据权限过滤条件（基于资源类型绑定）
        
        使用 data_scope_utils 中的统一实现
        
        :param db: 数据库会话
        :param user_info: 用户信息字典
        :return: 数据权限过滤条件字典
        """
        return await get_data_scope_filter(db, cls.RESOURCE_TYPE, user_info)
    
    @classmethod
    def _apply_data_scope_to_query(
        cls,
        query,
        data_scope_filter: Dict[str, Any],
        dept_field: str = "sys_dept_id",
        user_field: str = "sys_creator_id"
    ):
        """
        将数据权限过滤条件应用到查询
        
        使用 data_scope_utils 中的统一实现
        
        :param query: SQLAlchemy查询对象
        :param data_scope_filter: 数据权限过滤条件
        :param dept_field: 部门字段名
        :param user_field: 用户字段名
        :return: 应用过滤后的查询对象
        """
        conditions = apply_data_scope_to_conditions(
            cls.model, data_scope_filter, dept_field, user_field
        )
        for condition in conditions:
            query = query.where(condition)
        return query
    
    @classmethod
    async def export_to_excel_with_data_scope(
        cls,
        db: AsyncSession,
        data_converter: Optional[Callable[[Any], Dict[str, Any]]] = None,
        dept_field: str = "dept_id",
        user_field: str = "user_id"
    ) -> BytesIO:
        """
        导出数据到Excel（带数据权限过滤）
        
        自动从上下文获取当前用户信息和请求信息，无需手动传递任何参数
        
        :param db: 数据库会话
        :param data_converter: 数据转换函数
        :param dept_field: 部门字段名
        :param user_field: 用户字段名
        :return: Excel文件的BytesIO对象
        """
        # 从上下文获取用户信息和请求信息
        user_info = get_current_user_info_from_context()
        if not user_info:
            # 如果没有用户信息，返回空Excel
            return ExcelHandler.export_to_excel([], cls.excel_columns, cls.excel_sheet_name)
        
        # 获取数据权限过滤条件（优先使用资源类型绑定）
        data_scope_filter = await cls._get_data_scope_filter(db, user_info)
        
        # 构建查询
        query = select(cls.model).where(cls.model.is_deleted == False)  # noqa: E712
        
        # 应用数据权限过滤
        query = cls._apply_data_scope_to_query(
            query=query,
            data_scope_filter=data_scope_filter,
            dept_field=dept_field,
            user_field=user_field
        )
        
        # 执行查询
        result = await db.execute(
            query.order_by(desc(cls.model.sort), desc(cls.model.sys_create_datetime))
        )
        items = result.scalars().all()
        
        # 转换数据
        if data_converter:
            data = [data_converter(item) for item in items]
        else:
            data = [
                {field: getattr(item, field, "") for field in cls.excel_columns.keys()}
                for item in items
            ]
        
        return ExcelHandler.export_to_excel(data, cls.excel_columns, cls.excel_sheet_name)
    
    # ==================== 字段权限（列权限）相关方法 ====================
    
    @classmethod
    async def apply_field_permissions_auto(
        cls,
        data: Any,
        db: AsyncSession,
        merge_strategy: str = "most_permissive"
    ) -> Any:
        """
        自动应用字段权限过滤（从上下文获取角色）
        
        :param data: 数据（单个对象或列表）
        :param db: 数据库会话
        :param merge_strategy: 权限合并策略（most_permissive/most_restrictive）
        :return: 过滤后的数据
        """
        from utils.context import get_current_user_info_from_context
        
        # 从上下文获取用户信息
        user_info = get_current_user_info_from_context()
        if not user_info or not user_info.get('role_ids'):
            return data
        
        # 应用字段权限
        return await cls.apply_field_permissions(
            data=data,
            role_ids=user_info['role_ids'],
            db=db,
            merge_strategy=merge_strategy
        )
    
    @classmethod
    async def apply_field_permissions(
        cls,
        data: Any,
        role_ids: List[str],
        db: AsyncSession,
        merge_strategy: str = "most_permissive"
    ) -> Any:
        """
        应用字段权限过滤
        
        :param data: 数据（单个对象或列表）
        :param role_ids: 角色ID列表
        :param db: 数据库会话
        :param merge_strategy: 权限合并策略（most_permissive/most_restrictive）
        :return: 过滤后的数据
        """
        if not cls.RESOURCE_TYPE or not role_ids:
            return data
        
        # 获取字段权限配置
        field_perms = await cls._get_field_permissions(role_ids, db, merge_strategy)
        
        # 如果没有配置字段权限，直接返回原数据
        if not field_perms:
            return data
        
        # 处理单个对象或列表
        if isinstance(data, list):
            return [cls._filter_fields(item, field_perms) for item in data]
        else:
            return cls._filter_fields(data, field_perms)
    
    @classmethod
    async def _get_field_permissions(
        cls,
        role_ids: List[str],
        db: AsyncSession,
        merge_strategy: str = "most_permissive"
    ) -> Dict[str, Dict]:
        """获取并合并字段权限配置"""
        from core.resource_scope.field_permission.service import ResourceFieldPermissionService
        from app.field_permission_cache import FieldPermissionCache
        
        # 尝试从缓存获取
        cached_perms = await FieldPermissionCache.get_merged(role_ids, cls.RESOURCE_TYPE)
        if cached_perms is not None:
            return cached_perms
        
        # 获取所有角色的字段权限配置
        configs = await ResourceFieldPermissionService.get_by_roles_and_resource(
            db, role_ids, cls.RESOURCE_TYPE
        )
        
        if not configs:
            return {}
        
        # 合并权限
        merged_perms = await ResourceFieldPermissionService.merge_field_permissions(
            configs, merge_strategy
        )
        
        # 缓存结果
        await FieldPermissionCache.set_merged(role_ids, cls.RESOURCE_TYPE, merged_perms)
        
        return merged_perms
    
    @classmethod
    def _filter_fields(cls, item: Any, field_perms: Dict[str, Dict]) -> Dict:
        """
        过滤字段
        
        :param item: 数据项（可以是字典或 ORM 对象）
        :param field_perms: 字段权限配置
        :return: 过滤后的字典
        """
        # 转换为字典
        if hasattr(item, '__dict__'):
            item_dict = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
        elif hasattr(item, 'dict'):
            item_dict = item.dict()
        elif isinstance(item, dict):
            item_dict = item
        else:
            return item
        
        filtered = {}
        for field_name, value in item_dict.items():
            perm = field_perms.get(field_name, {})
            permission_type = perm.get('permission', 'read')
            
            if permission_type == 'hidden':
                # 隐藏字段，不返回
                continue
            elif permission_type == 'masked':
                # 脱敏处理
                filtered[field_name] = cls._mask_value(value, perm.get('mask_rule'))
            else:
                # read 或 write 权限，正常返回
                filtered[field_name] = value
        
        return filtered
    
    @classmethod
    def _mask_value(cls, value: Any, mask_rule: Optional[str]) -> str:
        """
        脱敏处理
        
        :param value: 原始值
        :param mask_rule: 脱敏规则
        :return: 脱敏后的值
        """
        if not value:
            return value
        
        value_str = str(value)
        
        if mask_rule == "phone":
            # 手机号脱敏：138****5678
            if len(value_str) == 11:
                return f"{value_str[:3]}****{value_str[-4:]}"
        elif mask_rule == "email":
            # 邮箱脱敏：abc***@example.com
            if "@" in value_str:
                local, domain = value_str.split("@", 1)
                if len(local) > 3:
                    return f"{local[:3]}***@{domain}"
                return f"{local[0]}***@{domain}"
        elif mask_rule == "id_card":
            # 身份证脱敏：110***********1234
            if len(value_str) >= 8:
                return f"{value_str[:3]}***********{value_str[-4:]}"
        elif mask_rule == "name":
            # 姓名脱敏：张*
            if len(value_str) > 1:
                return f"{value_str[0]}*"
            return "*"
        
        # 默认脱敏：显示前后各2个字符
        if len(value_str) > 4:
            return f"{value_str[:2]}***{value_str[-2:]}"
        return "***"
