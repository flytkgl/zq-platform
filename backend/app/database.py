import logging
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,  # 连接池常驻连接数（减少以避免连接耗尽）
    max_overflow=10,  # 超出pool_size后可创建的连接数（总计最多15）
    pool_timeout=30,  # 获取连接的超时时间（秒）
    pool_recycle=600,  # 连接回收时间（秒），更积极地回收空闲连接
    pool_pre_ping=True,  # 使用前检查连接是否有效，自动重连
    pool_reset_on_return="rollback",  # 连接归还时重置状态
)


# 连接池监控事件
@event.listens_for(engine.sync_engine, "checkout")
def _on_checkout(dbapi_conn, connection_rec, connection_proxy):
    pool = engine.sync_engine.pool
    logger.debug(
        f"[Pool] checkout: size={pool.size()}, checkedin={pool.checkedin()}, "
        f"checkedout={pool.checkedout()}, overflow={pool.overflow()}"
    )


@event.listens_for(engine.sync_engine, "checkin")
def _on_checkin(dbapi_conn, connection_rec):
    pool = engine.sync_engine.pool
    logger.debug(
        f"[Pool] checkin: size={pool.size()}, checkedin={pool.checkedin()}, "
        f"checkedout={pool.checkedout()}, overflow={pool.overflow()}"
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """获取数据库会话的依赖函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_transaction() -> AsyncSession:
    """
    获取带事务的数据库会话依赖函数
    
    使用方式：
    @router.post("/")
    async def create_something(db: AsyncSession = Depends(get_db_transaction)):
        # 所有数据库操作在同一事务中
        # 如果发生异常，自动回滚
        # 如果成功完成，自动提交
        ...
    
    注意：使用此依赖时，Service层的方法不应调用commit()，
    因为事务会在API结束时统一提交或回滚。
    可以使用BaseService的_no_commit版本方法，或手动控制。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def transaction(db: AsyncSession):
    """
    事务上下文管理器，用于在API中包装多个操作
    
    使用方式：
    @router.post("/")
    async def create_something(db: AsyncSession = Depends(get_db)):
        async with transaction(db):
            # 所有操作在同一事务中
            await SomeService.create_no_commit(db, data1)
            await OtherService.create_no_commit(db, data2)
            # 如果发生异常，自动回滚
            # 如果成功完成，自动提交
    """
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
