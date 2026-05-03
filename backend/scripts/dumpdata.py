#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: 臧成龙
@Contact: 939589097@qq.com
@Time: 2025-12-31
@File: dumpdata.py
@Desc: 数据导出脚本 - 类似 Django 的 dumpdata - 使用方法: python scripts/dumpdata.py [app_name] > data.json
"""
"""
数据导出脚本 - 类似 Django 的 dumpdata
使用方法: python scripts/dumpdata.py [app_name] > data.json
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal, Base


def auto_import_models():
    """自动导入所有模型"""
    import importlib
    project_root = Path(__file__).parent.parent
    
    # 需要扫描的目录
    scan_dirs = ["zq_demo", "core", "scheduler", "online_dev", "ai_platform"]
    
    for scan_dir in scan_dirs:
        scan_path = project_root / scan_dir
        if not scan_path.exists():
            continue
        
        # 递归查找所有 model.py 文件
        for model_file in scan_path.rglob("*model.py"):
            # 计算模块路径
            relative_path = model_file.relative_to(project_root)
            module_path = str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")
            
            try:
                importlib.import_module(module_path)
                print(f"导入模型: {module_path}", file=sys.stderr)
            except ImportError as e:
                print(f"警告: 导入失败 {module_path}: {e}", file=sys.stderr)


# 自动导入所有模型
auto_import_models()


class DateTimeEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理日期时间和 Decimal"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        # 处理 date 类型
        from datetime import date
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


async def dump_table(session: AsyncSession, model_class):
    """导出单个表的数据"""
    from sqlalchemy import select
    
    result = await session.execute(select(model_class))
    items = result.scalars().all()
    
    table_data = []
    for item in items:
        # 获取所有列
        item_dict = {}
        for column in inspect(model_class).columns:
            value = getattr(item, column.name)
            item_dict[column.name] = value
        
        table_data.append({
            "model": f"{model_class.__module__}.{model_class.__name__}",
            "pk": item.id,
            "fields": item_dict
        })
    
    return table_data


async def dump_all_data(app_name: str = None, exclude_tables: list = None):
    """导出所有数据或指定应用的数据
    
    Args:
        app_name: 应用名称（可选），如 core、scheduler
        exclude_tables: 排除的表名列表（可选）
    """
    import logging
    
    exclude_tables = exclude_tables or []
    
    # 临时禁用 SQLAlchemy 的日志输出
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    original_level = sqlalchemy_logger.level
    sqlalchemy_logger.setLevel(logging.WARNING)
    
    all_data = []
    
    try:
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
                    print(f"跳过表: {model_class.__tablename__}", file=sys.stderr)
                    continue
                
                models.append(model_class)
            
            # 按表名排序
            models.sort(key=lambda m: m.__tablename__)
            
            # 导出每个表
            for model_class in models:
                print(f"导出表: {model_class.__tablename__}", file=sys.stderr)
                table_data = await dump_table(session, model_class)
                all_data.extend(table_data)
                print(f"  - 导出 {len(table_data)} 条记录", file=sys.stderr)
    finally:
        # 恢复 SQLAlchemy 日志级别
        sqlalchemy_logger.setLevel(original_level)
    
    return all_data


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导出数据到 JSON 文件')
    parser.add_argument('app_name', nargs='?', help='应用名称（可选），如 core、scheduler')
    parser.add_argument('-o', '--output', help='输出文件路径（可选），不指定则输出到标准输出')
    parser.add_argument('-f', '--force', action='store_true', help='强制覆盖已存在的文件')
    parser.add_argument('-e', '--exclude', action='append', default=[], 
                        help='排除的表名，可多次使用，如: -e scheduler_log -e core_operation_log')
    
    args = parser.parse_args()
    
    if args.app_name:
        print(f"导出应用: {args.app_name}", file=sys.stderr)
    else:
        print("导出所有数据", file=sys.stderr)
    
    if args.exclude:
        print(f"排除表: {', '.join(args.exclude)}", file=sys.stderr)
    
    data = await dump_all_data(args.app_name, exclude_tables=args.exclude)
    
    # 生成 JSON 字符串
    json_str = json.dumps(data, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
    
    # 输出到文件或标准输出
    if args.output:
        output_path = Path(args.output)
        
        # 检查文件是否存在
        if output_path.exists() and not args.force:
            print(f"\n错误: 文件已存在: {output_path}", file=sys.stderr)
            print("使用 -f 或 --force 参数强制覆盖", file=sys.stderr)
            sys.exit(1)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        print(f"\n总计导出 {len(data)} 条记录", file=sys.stderr)
        print(f"已保存到: {output_path}", file=sys.stderr)
    else:
        # 输出到标准输出
        print(json_str)
        print(f"\n总计导出 {len(data)} 条记录", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
