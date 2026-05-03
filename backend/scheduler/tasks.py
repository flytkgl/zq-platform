#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scheduler Tasks - 定时任务函数示例
定义可被调度器调用的任务函数
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def test_task(job_code: str = None, word: str = None, **kwargs):
    """
    测试任务
    
    这是一个简单的测试任务，用于验证调度器是否正常工作。
    
    Args:
        job_code: 任务编码（由调度器自动传入）
        **kwargs: 其他参数
    """
    logger.info(f"[{job_code}-{word}] 测试任务执行开始: {datetime.now()}")
    
    # 模拟任务执行
    import asyncio
    await asyncio.sleep(10)
    
    logger.info(f"[{job_code}] 测试任务执行完成: {datetime.now()}")
    return f"测试任务执行成功: {datetime.now()}"


async def cleanup_task(job_code: str = None, days: int = 30, **kwargs):
    """
    清理任务
    
    清理过期的日志数据。
    
    Args:
        job_code: 任务编码（由调度器自动传入）
        days: 保留最近N天的数据
        **kwargs: 其他参数
    """
    logger.info(f"[{job_code}] 清理任务执行开始，保留最近 {days} 天数据")
    
    try:
        from datetime import timedelta
        from sqlalchemy import select, delete
        from app.database import AsyncSessionLocal
        from scheduler.model import SchedulerLog
        
        cutoff = datetime.now() - timedelta(days=days)
        
        async with AsyncSessionLocal() as db:
            # 删除过期日志
            result = await db.execute(
                select(SchedulerLog).where(SchedulerLog.start_time < cutoff)
            )
            logs = result.scalars().all()
            count = len(logs)
            
            for log in logs:
                await db.delete(log)
            
            await db.commit()
            
        logger.info(f"[{job_code}] 清理任务执行完成，删除了 {count} 条日志")
        return f"清理了 {count} 条过期日志"
    except Exception as e:
        logger.error(f"[{job_code}] 清理任务执行失败: {str(e)}")
        raise


def sync_test_task(job_code: str = None, **kwargs):
    """
    同步测试任务
    
    这是一个同步任务示例，用于演示同步任务的使用。
    
    Args:
        job_code: 任务编码（由调度器自动传入）
        **kwargs: 其他参数
    """
    import time
    
    logger.info(f"[{job_code}] 同步测试任务执行开始: {datetime.now()}")
    
    # 模拟任务执行
    time.sleep(1)
    
    logger.info(f"[{job_code}] 同步测试任务执行完成: {datetime.now()}")
    return f"同步测试任务执行成功: {datetime.now()}"


async def restore_database_task(
    job_code: str = None,
    file_path: str = './db_init.json',
    app_name: str = None,
    clear_before_restore: bool = True,
    exclude_tables: list = None,
    **kwargs
):
    """
    数据库数据恢复任务
    
    从 JSON 文件恢复数据库数据，类似 Django 的 loaddata 命令。
    
    Args:
        job_code: 任务编码（由调度器自动传入）
        file_path: JSON 数据文件路径（必填）
        app_name: 应用名称过滤（可选），如 core、scheduler，只恢复指定应用的数据
        clear_before_restore: 恢复前是否清空目标表（默认 True）
        exclude_tables: 排除的表名列表（可选），如 ['scheduler_log', 'core_operation_log']
        **kwargs: 其他参数（包含 task_logger）
    
    Returns:
        str: 恢复结果摘要
    
    Raises:
        ValueError: 文件路径未指定或文件不存在
        Exception: 数据恢复过程中的错误
    """
    exclude_tables = exclude_tables or ['core_city', 'core_street', 'core_village', 'core_area','core_province', 'core_scheduler_job', 'core_scheduler_log']
    import json
    from pathlib import Path
    from typing import Dict, Any
    
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import delete
    from app.database import AsyncSessionLocal, Base
    from scheduler.task_utils import TaskLoggerWrapper
    
    # 创建日志包装器：同时输出到控制台和实时日志
    log = TaskLoggerWrapper(job_code, kwargs.get('task_logger'))
    
    await log.info(f"数据库恢复任务开始执行")
    
    # 验证文件路径
    if not file_path:
        raise ValueError("file_path 参数不能为空")
    
    data_file = Path(file_path)
    if not data_file.exists():
        raise ValueError(f"数据文件不存在: {file_path}")
    
    if not data_file.suffix.lower() == '.json':
        raise ValueError(f"只支持 JSON 格式的数据文件: {file_path}")
    
    await log.info(f"从文件加载数据: {file_path}")
    
    def parse_datetime(value):
        """解析日期时间字符串"""
        if isinstance(value, str):
            # 尝试解析 ISO 格式的日期时间字符串
            try:
                # 支持多种格式
                if 'T' in value or ' ' in value:
                    # 包含时间部分
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif len(value) == 10 and value.count('-') == 2:
                    # 只有日期部分 YYYY-MM-DD
                    from datetime import date
                    return date.fromisoformat(value)
            except (ValueError, AttributeError):
                pass
        return value
    
    async def auto_import_models():
        """自动加载所有模型类定义"""
        import importlib
        project_root = Path(__file__).parent.parent
        
        scan_dirs = ["zq_demo", "core", "scheduler", "online_dev", "ai_platform"]
        loaded_count = 0
        
        for scan_dir in scan_dirs:
            scan_path = project_root / scan_dir
            if not scan_path.exists():
                continue
            
            for model_file in scan_path.rglob("*model.py"):
                relative_path = model_file.relative_to(project_root)
                module_path = str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")
                
                try:
                    importlib.import_module(module_path)
                    loaded_count += 1
                except ImportError as e:
                    logger.warning(f"[{job_code}] 加载模型定义失败 {module_path}: {e}")
        
        await log.info(f"已加载 {loaded_count} 个模型定义文件")
    
    try:
        # 自动加载所有模型类定义（不是导入数据）
        await log.info(f"开始加载模型定义...")
        await auto_import_models()
        
        # 读取 JSON 文件
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        await log.info(f"读取到 {len(data)} 条记录")
        
        # 构建模型映射
        model_map: Dict[str, Any] = {}
        for mapper in Base.registry.mappers:
            model_class = mapper.class_
            model_key = f"{model_class.__module__}.{model_class.__name__}"
            model_map[model_key] = model_class
        
        # 如果指定了 app_name，过滤数据
        if app_name:
            data = [item for item in data if item.get("model", "").startswith(app_name)]
            await log.info(f"过滤后剩余 {len(data)} 条记录（应用: {app_name})")
        
        # 排除指定的表
        if exclude_tables:
            original_count = len(data)
            data = [
                item for item in data 
                if not (model_map.get(item.get("model")) and 
                        model_map[item.get("model")].__tablename__ in exclude_tables)
            ]
            excluded_count = original_count - len(data)
            if excluded_count > 0:
                await log.info(f"排除 {excluded_count} 条记录（表: {', '.join(exclude_tables)})")
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        from sqlalchemy import text
        
        # 阶段1：清空表（每个表独立事务，避免长时间持有锁）
        if clear_before_restore:
            tables_to_clear = set()
            for item in data:
                model_name = item.get("model")
                if model_name in model_map:
                    tables_to_clear.add(model_name)
            
            # 按表名排序，便于追踪进度
            sorted_tables = sorted(tables_to_clear, key=lambda x: model_map[x].__tablename__)
            total_tables = len(sorted_tables)
            await log.info(f"准备清空 {total_tables} 个表...")
            
            # 每个表独立事务清空
            for idx, model_name in enumerate(sorted_tables, 1):
                model_class = model_map[model_name]
                table_name = model_class.__tablename__
                await log.info(f"[{idx}/{total_tables}] 清空表: {table_name}")
                
                async with AsyncSessionLocal() as session:
                    try:
                        # 使用 TRUNCATE CASCADE 处理外键依赖
                        await session.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        # 如果 TRUNCATE 失败，尝试 DELETE
                        await log.warning(f"TRUNCATE 失败，使用 DELETE: {e}")
                        try:
                            await session.execute(delete(model_class))
                            await session.commit()
                        except Exception as e2:
                            await log.error(f"DELETE 也失败: {e2}")
                            await session.rollback()
            
            await log.info(f"已清空 {total_tables} 个表")
        
        # 阶段2：导入数据（分批提交，每批独立事务）
        total_records = len(data)
        await log.info(f"开始导入 {total_records} 条记录...")
        
        batch_size = 500
        batch = []
        
        for idx, item in enumerate(data, 1):
            model_name = item.get("model")
            fields = item.get("fields", {})
            
            if model_name not in model_map:
                skipped_count += 1
                continue
            
            model_class = model_map[model_name]
            
            # 转换日期时间字段（对所有字段值尝试转换）
            for key, value in fields.items():
                fields[key] = parse_datetime(value)
            
            batch.append((model_class, fields))
            
            # 每 batch_size 条提交一次
            if len(batch) >= batch_size:
                async with AsyncSessionLocal() as session:
                    try:
                        for model_class, fields in batch:
                            instance = model_class(**fields)
                            session.add(instance)
                        await session.commit()
                        success_count += len(batch)
                    except Exception as e:
                        await log.error(f"批量导入失败: {e}")
                        error_count += len(batch)
                        await session.rollback()
                
                batch = []
                progress = round(idx / total_records * 100, 1)
                await log.info(f"进度: {progress}% ({idx}/{total_records}) - 成功: {success_count}, 失败: {error_count}, 跳过: {skipped_count}")
        
        # 提交剩余的数据
        if batch:
            async with AsyncSessionLocal() as session:
                try:
                    for model_class, fields in batch:
                        instance = model_class(**fields)
                        session.add(instance)
                    await session.commit()
                    success_count += len(batch)
                except Exception as e:
                    await log.error(f"最后批次导入失败: {e}")
                    error_count += len(batch)
                    await session.rollback()
        
        result = f"恢复完成: 成功 {success_count} 条, 失败 {error_count} 条, 跳过 {skipped_count} 条"
        await log.info(f"{result}")
        return result
        
    except Exception as e:
        await log.error(f"数据库恢复任务执行失败: {str(e)}")
        raise


async def backup_database_task(
    job_code: str = None,
    output_path: str = None,
    app_name: str = None,
    exclude_tables: list = None,
    **kwargs
):
    """
    数据库数据备份任务
    
    将数据库数据导出到 JSON 文件，类似 Django 的 dumpdata 命令。
    
    Args:
        job_code: 任务编码（由调度器自动传入）
        output_path: 输出文件路径（可选），默认为 backups/backup_YYYYMMDD_HHMMSS.json
        app_name: 应用名称过滤（可选），如 core、scheduler，只备份指定应用的数据
        exclude_tables: 排除的表名列表（可选），如 ['scheduler_log', 'core_operation_log']
        **kwargs: 其他参数
    
    Returns:
        str: 备份结果摘要，包含文件路径和记录数
    """
    exclude_tables = exclude_tables or []
    import json
    from pathlib import Path
    from decimal import Decimal
    from datetime import date
    
    from sqlalchemy import inspect
    from app.database import AsyncSessionLocal, Base
    
    logger.info(f"[{job_code}] 数据库备份任务开始执行")
    
    class DateTimeEncoder(json.JSONEncoder):
        """自定义 JSON 编码器"""
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            return super().default(obj)
    
    def auto_import_models():
        """自动导入所有模型"""
        import importlib
        project_root = Path(__file__).parent.parent
        
        scan_dirs = ["zq_demo", "core", "scheduler", "online_dev", "ai_platform"]
        
        for scan_dir in scan_dirs:
            scan_path = project_root / scan_dir
            if not scan_path.exists():
                continue
            
            for model_file in scan_path.rglob("*model.py"):
                relative_path = model_file.relative_to(project_root)
                module_path = str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")
                
                try:
                    importlib.import_module(module_path)
                except ImportError as e:
                    logger.warning(f"[{job_code}] 导入模型失败 {module_path}: {e}")
    
    try:
        # 自动导入所有模型
        auto_import_models()
        
        # 确定输出路径
        if output_path:
            output_file = Path(output_path)
        else:
            project_root = Path(__file__).parent.parent
            backups_dir = project_root / "backups"
            backups_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{app_name}_{timestamp}.json" if app_name else f"backup_{timestamp}.json"
            output_file = backups_dir / filename
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        all_data = []
        
        async with AsyncSessionLocal() as session:
            # 获取所有模型
            models = []
            for mapper in Base.registry.mappers:
                model_class = mapper.class_
                
                # 如果指定了 app_name，只导出该应用的模型
                if app_name:
                    module_name = model_class.__module__
                    if not module_name.startswith(app_name):
                        continue
                
                # 排除指定的表
                if model_class.__tablename__ in exclude_tables:
                    logger.info(f"[{job_code}] 跳过表: {model_class.__tablename__}")
                    continue
                
                models.append(model_class)
            
            # 按表名排序
            models.sort(key=lambda m: m.__tablename__)
            
            logger.info(f"[{job_code}] 准备备份 {len(models)} 个表")
            
            # 导出每个表
            from sqlalchemy import select
            
            for model_class in models:
                logger.info(f"[{job_code}] 备份表: {model_class.__tablename__}")
                
                result = await session.execute(select(model_class))
                items = result.scalars().all()
                
                for item in items:
                    item_dict = {}
                    for column in inspect(model_class).columns:
                        value = getattr(item, column.name)
                        item_dict[column.name] = value
                    
                    all_data.append({
                        "model": f"{model_class.__module__}.{model_class.__name__}",
                        "pk": item.id if hasattr(item, 'id') else None,
                        "fields": item_dict
                    })
                
                logger.info(f"[{job_code}]   - 备份 {len(items)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        result = f"备份完成: 共 {len(all_data)} 条记录，保存到 {output_file}"
        logger.info(f"[{job_code}] {result}")
        return result
        
    except Exception as e:
        logger.error(f"[{job_code}] 数据库备份任务执行失败: {str(e)}")
        raise
