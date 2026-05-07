#!/bin/bash
# RAG-Anything Server 启动脚本
# 在容器启动时自动运行数据库迁移

set -e

echo "=========================================="
echo "RAG-Anything Server 启动"
echo "=========================================="

# 等待数据库就绪
echo ""
echo "⏳ 等待 PostgreSQL 就绪..."
for i in $(seq 1 30); do
    if python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os

async def check_db():
    try:
        # 使用环境变量中的 DATABASE_URL
        db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://admin:admin_2617@db:5432/raganything_test')
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            await conn.execute(asyncio.wrap_future(lambda: None))
        await engine.dispose()
        return True
    except:
        return False

import sys
sys.exit(0 if asyncio.run(check_db()) else 1)
" 2>/dev/null; then
        echo "✅ PostgreSQL 已就绪"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL 连接超时"
        exit 1
    fi
    
    echo "   等待中... ($i/30)"
    sleep 2
done

# 初始化数据库（创建所有表）
echo ""
echo "🔧 初始化数据库（创建表结构）..."
python -c "
import asyncio
from server.models.database import init_db

async def main():
    try:
        await init_db()
        print('✅ 数据库表结构创建成功')
    except Exception as e:
        print(f'⚠️  数据库初始化失败: {e}')
        print('   如果表已存在，可以忽略此错误')

asyncio.run(main())
" || {
    echo "⚠️  数据库初始化失败，但继续启动应用"
}

# 检查是否需要创建超级管理员
echo ""
echo "👤 检查超级管理员..."
python scripts/create_super_admin.py --auto-create || {
    echo "⚠️  超级管理员创建失败（可能已存在）"
}

echo ""
echo "✅ 初始化完成，启动应用..."
echo "=========================================="

# 启动 Uvicorn
exec uvicorn server.main:app --host 0.0.0.0 --port 8000
