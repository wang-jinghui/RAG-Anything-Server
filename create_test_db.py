import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def create_test_db():
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ 错误：DATABASE_URL 环境变量未设置")
            return
        
        # Parse database URL (postgresql+asyncpg://user:pass@host:port/dbname)
        # Remove 'postgresql+asyncpg://' prefix
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "")
        
        # Parse credentials and connection info
        # Format: user:password@host:port/dbname
        auth_part, _, rest = database_url.partition("@")
        user, _, password = auth_part.partition(":")
        
        host_port_db = rest.split("/")
        host_port = host_port_db[0]
        dbname = host_port_db[1] if len(host_port_db) > 1 else "postgres"
        
        host, _, port = host_port.partition(":")
        
        # Connect to postgres database first
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database='postgres'
        )
        print("✅ PostgreSQL 连接成功！")
        
        # 检查数据库是否存在
        databases = await conn.fetch("SELECT datname FROM pg_database WHERE datname = 'raganything_test'")
        
        if not databases:
            print("📝 正在创建测试数据库 'raganything_test'...")
            # 需要单独的连接来创建数据库（不能在事务中）
            await conn.execute("COMMIT")  # 结束当前事务
            await conn.execute("CREATE DATABASE raganything_test")
            print("✅ 测试数据库创建成功！")
        else:
            print("✅ 测试数据库 'raganything_test' 已存在")
            # 清理旧数据
            print("🧹 清理旧数据...")
            await conn.execute("COMMIT")
            await conn.execute("DROP DATABASE IF EXISTS raganything_test")
            await conn.execute("CREATE DATABASE raganything_test")
            print("✅ 数据库已重置！")
        
        await conn.close()
        print("\n🎉 现在可以运行测试了！")
        print("命令：G:\\Anaconda3\\envs\\mkbms\\python.exe -m pytest tests/test_smoke.py -v")
        
    except Exception as e:
        print(f"❌ 错误：{e}")

if __name__ == "__main__":
    asyncio.run(create_test_db())
