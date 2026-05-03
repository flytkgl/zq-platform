import utils.openapi_patch  # noqa: F401  # FastAPI OpenAPI schema 兼容性补丁，必须在首行导入

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from utils.redis import RedisClient
from zq_demo.router import router as zq_demo_router
from core.router import router as core_router
from scheduler.router import router as scheduler_router
from online_dev.router import router as online_form_router
from core.websocket.router import router as websocket_router
from utils.auth_middleware import AuthPermissionMiddleware


# 全局OAuth2方案，用于Swagger显示小锁图标
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/core/auth/login/oauth2", auto_error=False)


async def register_published_forms():
    """启动时注册已发布的表单资源类型"""
    from app.database import AsyncSessionLocal
    from online_dev.form_manager.service import FormService
    
    async with AsyncSessionLocal() as db:
        await FormService.register_published_forms_to_registry(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时注册已发布的表单资源类型
    await register_published_forms()
    
    # 预热系统配置到 Redis
    from app.config_manager import config_manager
    await config_manager.warmup()
    
    # 启动定时任务调度器 (APScheduler 4.x)
    if getattr(settings, 'ENABLE_SCHEDULER', True):
        from apscheduler import AsyncScheduler
        from scheduler.service import scheduler_service
        
        scheduler = AsyncScheduler()
        async with scheduler:
            await scheduler.start_in_background()
            scheduler_service.set_scheduler(scheduler)
            app.state.scheduler = scheduler
            
            # 加载数据库中的任务
            await scheduler_service.load_jobs_from_db()
            
            # 恢复未完成的工作流延时任务
            # from online_dev.workflow.engine.delay_callback import recover_pending_delay_tasks
            # await recover_pending_delay_tasks()
            
            yield
            
            # 关闭时
            scheduler_service.set_running(False)
    else:
        yield
    
    await RedisClient.close()

app = FastAPI(
    title=settings.APP_NAME,
    description="一个简单的FastAPI CRUD示例",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

# 添加全局认证中间件（白名单内的路由无需认证）
app.add_middleware(AuthPermissionMiddleware)

# 注册路由（带全局OAuth2依赖，用于Swagger显示小锁图标）
app.include_router(zq_demo_router, prefix="/api/zq_demo", dependencies=[Depends(oauth2_scheme)])
app.include_router(core_router, prefix="/api/core", dependencies=[Depends(oauth2_scheme)])
app.include_router(online_form_router, prefix="/api/online_dev", dependencies=[Depends(oauth2_scheme)])

app.include_router(scheduler_router, prefix="/api", dependencies=[Depends(oauth2_scheme)])
# WebSocket路由（不需要OAuth2依赖，WebSocket自己处理认证）
app.include_router(websocket_router)


@app.get("/", tags=["根路径"])
async def root():
    """API根路径"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "env": settings.ENV,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
