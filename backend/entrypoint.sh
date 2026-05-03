#!/bin/bash
# ============================================
# ZQ Platform 后端启动入口
# 自动检测数据库状态 → 生成迁移 → 执行迁移 → 启动应用
# ============================================

set -e

echo "=========================================="
echo "  ZQ Platform Backend"
echo "=========================================="

echo "[1/2] 数据库初始化..."

# 检查 versions 目录是否有迁移文件
MIGRATION_COUNT=$(ls alembic/versions/*.py 2>/dev/null | wc -l)

if [ "$MIGRATION_COUNT" -eq "0" ]; then
    echo "  未发现迁移文件，自动生成..."
    python -m alembic revision --autogenerate -m "initial" 2>&1 | tail -3
fi

# 执行迁移
python -m alembic upgrade head 2>&1 || {
    echo "  [WARN] 迁移失败，5秒后重试..."
    sleep 5
    python -m alembic upgrade head 2>&1 || echo "  [WARN] 迁移再次失败，跳过"
}

# 检查是否需要导入初始数据（仅首次部署时）
USER_COUNT=$(python -c "
import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text
async def check():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(text(\"SELECT COUNT(*) FROM core_user\"))
            print(result.scalar())
    except:
        print(0)
asyncio.run(check())
" 2>/dev/null || echo "0")

if [ "$USER_COUNT" -eq "0" ] 2>/dev/null; then
    if [ -f "db_init.json" ]; then
        echo "  首次部署，导入初始化数据..."
        python scripts/loaddata.py db_init.json 2>&1
    else
        echo "  [WARN] 未找到 db_init.json，跳过数据导入"
    fi
else
    echo "  数据库已有数据 ($USER_COUNT 个用户)，跳过导入"
fi

echo "  数据库就绪"

echo "[2/2] 启动 FastAPI..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
