#!/bin/bash
# RAG-Anything Server Docker 快速启动脚本

set -e

echo "=========================================="
echo "RAG-Anything Server Docker 部署"
echo "=========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误: Docker Compose 未安装"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 版本: $(docker --version)"
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose 版本: $(docker-compose --version)"
    COMPOSE_CMD="docker-compose"
else
    echo "✅ Docker Compose 版本: $(docker compose version)"
    COMPOSE_CMD="docker compose"
fi
echo ""

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "正在从 .env.example 创建 .env..."
    cp .env.example .env
    echo ""
    echo "❗ 重要: 请编辑 .env 文件并配置以下参数:"
    echo "   - JWT_SECRET_KEY (生产环境必须修改!)"
    echo "   - OPENAI_API_KEY (如果使用 OpenAI)"
    echo "   - POSTGRES_PASSWORD"
    echo "   - NEO4J_PASSWORD"
    echo ""
    read -p "按回车键继续，或按 Ctrl+C 退出以编辑 .env 文件..."
fi

# 询问用户操作
echo "请选择操作:"
echo "1. 构建并启动所有服务"
echo "2. 仅启动已构建的服务"
echo "3. 停止所有服务"
echo "4. 停止并删除所有数据（谨慎！）"
echo "5. 查看服务状态"
echo "6. 查看应用日志"
echo "7. 初始化数据库"
echo "8. 重新构建（无缓存）"
read -p "请输入选项 (1-8): " choice

case $choice in
    1)
        echo ""
        echo "🔨 正在构建 Docker 镜像..."
        $COMPOSE_CMD build
        
        echo ""
        echo "🚀 正在启动服务..."
        $COMPOSE_CMD up -d
        
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 10
        
        echo ""
        echo "📊 服务状态:"
        $COMPOSE_CMD ps
        
        echo ""
        echo "✅ 部署完成！"
        echo ""
        echo "访问以下地址:"
        echo "  - API 文档: http://localhost:8000/docs"
        echo "  - 健康检查: http://localhost:8000/health"
        echo "  - Neo4j Browser: http://localhost:7474"
        echo ""
        echo "下一步: 运行数据库迁移"
        echo "  $COMPOSE_CMD exec rag-server alembic upgrade head"
        echo "  $COMPOSE_CMD exec rag-server python scripts/create_super_admin.py"
        ;;
        
    2)
        echo ""
        echo "🚀 正在启动服务..."
        $COMPOSE_CMD up -d
        
        echo ""
        echo "✅ 服务已启动"
        $COMPOSE_CMD ps
        ;;
        
    3)
        echo ""
        echo "🛑 正在停止服务..."
        $COMPOSE_CMD down
        
        echo ""
        echo "✅ 服务已停止（数据已保留）"
        ;;
        
    4)
        echo ""
        echo "⚠️  警告: 此操作将删除所有数据！"
        read -p "确定要继续吗？(yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🗑️  正在停止并删除所有服务和数据..."
            $COMPOSE_CMD down -v
            
            echo ""
            echo "✅ 所有服务和数据已删除"
        else
            echo "❌ 操作已取消"
        fi
        ;;
        
    5)
        echo ""
        echo "📊 服务状态:"
        $COMPOSE_CMD ps
        ;;
        
    6)
        echo ""
        echo "📋 显示应用日志 (Ctrl+C 退出):"
        $COMPOSE_CMD logs -f rag-server
        ;;
        
    7)
        echo ""
        echo "🔧 正在初始化数据库..."
        $COMPOSE_CMD exec rag-server alembic upgrade head
        
        echo ""
        echo "👤 正在创建超级管理员..."
        $COMPOSE_CMD exec rag-server python scripts/create_super_admin.py
        
        echo ""
        echo "✅ 数据库初始化完成"
        ;;
        
    8)
        echo ""
        echo "🔨 正在重新构建镜像（无缓存）..."
        $COMPOSE_CMD build --no-cache
        
        echo ""
        echo "✅ 构建完成"
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "完成"
echo "=========================================="
