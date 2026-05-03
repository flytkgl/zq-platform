import asyncio
import importlib
import pkgutil
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.database import Base
from app.config import settings


def auto_import_models():
    """
    自动导入所有模块下的*model.py文件
    扫描项目根目录下所有以model结尾的py文件（如model.py、screen_model.py、material_model.py）
    """
    project_root = Path(__file__).parent.parent
    
    # 需要扫描的目录（可以添加更多）
    scan_dirs = ["zq_demo", "core", "scheduler", "online_dev", "ai_platform", "zq_smart_table"]
    
    for scan_dir in scan_dirs:
        scan_path = project_root / scan_dir
        if not scan_path.exists():
            continue
        
        # 递归查找所有以model结尾的py文件（如model.py、screen_model.py、material_model.py）
        for model_file in scan_path.rglob("*model.py"):
            # 计算模块路径，如 zq_demo.demo.model 或 core.screen_design.screen_model
            relative_path = model_file.relative_to(project_root)
            module_path = str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")
            
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                print(f"Warning: Failed to import {module_path}: {e}")


# 自动导入所有模型
auto_import_models()

config = context.config

# 设置数据库URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
