import asyncio
import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler.tasks import restore_database_task

async def main():
    print("=" * 80)
    print("开始执行数据库恢复任务...")
    print("=" * 80)
    
    try:
        result = await restore_database_task(
            job_code='test_restore',
            file_path='./db_init_0301.json',
            clear_before_restore=True,
            exclude_tables=['core_city', 'core_street', 'core_village', 'core_area','core_province', 'core_scheduler_job', 'core_scheduler_log']
        )
        print("\n" + "=" * 80)
        print("恢复任务完成！")
        print("=" * 80)
        print(f"结果: {result}")
    except Exception as e:
        print("\n" + "=" * 80)
        print("恢复任务失败！")
        print("=" * 80)
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
