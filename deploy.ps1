# RAG-Anything Server Docker 快速启动脚本 (PowerShell)
# 适用于 Windows 系统

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RAG-Anything Server Docker 部署" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否安装
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker 版本: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: Docker 未安装" -ForegroundColor Red
    Write-Host "请先安装 Docker Desktop: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

# 检查 Docker Compose 是否安装
try {
    $composeVersion = docker compose version 2>&1
    Write-Host "✅ Docker Compose 版本: $composeVersion" -ForegroundColor Green
    $COMPOSE_CMD = "docker compose"
} catch {
    try {
        $composeVersion = docker-compose --version
        Write-Host "✅ Docker Compose 版本: $composeVersion" -ForegroundColor Green
        $COMPOSE_CMD = "docker-compose"
    } catch {
        Write-Host "❌ 错误: Docker Compose 未安装" -ForegroundColor Red
        Write-Host "请确保 Docker Desktop 已安装并启用 Compose" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""

# 检查 .env 文件是否存在
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  警告: .env 文件不存在" -ForegroundColor Yellow
    Write-Host "正在从 .env.example 创建 .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "❗ 重要: 请编辑 .env 文件并配置以下参数:" -ForegroundColor Red
    Write-Host "   - JWT_SECRET_KEY (生产环境必须修改!)" -ForegroundColor Yellow
    Write-Host "   - OPENAI_API_KEY (如果使用 OpenAI)" -ForegroundColor Yellow
    Write-Host "   - POSTGRES_PASSWORD" -ForegroundColor Yellow
    Write-Host "   - NEO4J_PASSWORD" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按回车键继续，或按 Ctrl+C 退出以编辑 .env 文件"
}

# 询问用户操作
Write-Host "请选择操作:" -ForegroundColor Cyan
Write-Host "1. 构建并启动所有服务" -ForegroundColor White
Write-Host "2. 仅启动已构建的服务" -ForegroundColor White
Write-Host "3. 停止所有服务" -ForegroundColor White
Write-Host "4. 停止并删除所有数据（谨慎！）" -ForegroundColor White
Write-Host "5. 查看服务状态" -ForegroundColor White
Write-Host "6. 查看应用日志" -ForegroundColor White
Write-Host "7. 初始化数据库" -ForegroundColor White
Write-Host "8. 重新构建（无缓存）" -ForegroundColor White
$choice = Read-Host "请输入选项 (1-8)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🔨 正在构建 Docker 镜像..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD build"
        
        Write-Host ""
        Write-Host "🚀 正在启动服务..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD up -d"
        
        Write-Host ""
        Write-Host "⏳ 等待服务启动..." -ForegroundColor Cyan
        Start-Sleep -Seconds 10
        
        Write-Host ""
        Write-Host "📊 服务状态:" -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD ps"
        
        Write-Host ""
        Write-Host "✅ 部署完成！" -ForegroundColor Green
        Write-Host ""
        Write-Host "访问以下地址:" -ForegroundColor Cyan
        Write-Host "  - API 文档: http://localhost:8000/docs" -ForegroundColor White
        Write-Host "  - 健康检查: http://localhost:8000/health" -ForegroundColor White
        Write-Host "  - Neo4j Browser: http://localhost:7474" -ForegroundColor White
        Write-Host ""
        Write-Host "下一步: 运行数据库迁移" -ForegroundColor Yellow
        Write-Host "  $COMPOSE_CMD exec rag-server alembic upgrade head" -ForegroundColor White
        Write-Host "  $COMPOSE_CMD exec rag-server python scripts/create_super_admin.py" -ForegroundColor White
    }
    
    "2" {
        Write-Host ""
        Write-Host "🚀 正在启动服务..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD up -d"
        
        Write-Host ""
        Write-Host "✅ 服务已启动" -ForegroundColor Green
        Invoke-Expression "$COMPOSE_CMD ps"
    }
    
    "3" {
        Write-Host ""
        Write-Host "🛑 正在停止服务..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD down"
        
        Write-Host ""
        Write-Host "✅ 服务已停止（数据已保留）" -ForegroundColor Green
    }
    
    "4" {
        Write-Host ""
        Write-Host "⚠️  警告: 此操作将删除所有数据！" -ForegroundColor Red
        $confirm = Read-Host "确定要继续吗？(yes/no)"
        if ($confirm -eq "yes") {
            Write-Host "🗑️  正在停止并删除所有服务和数据..." -ForegroundColor Cyan
            Invoke-Expression "$COMPOSE_CMD down -v"
            
            Write-Host ""
            Write-Host "✅ 所有服务和数据已删除" -ForegroundColor Green
        } else {
            Write-Host "❌ 操作已取消" -ForegroundColor Yellow
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "📊 服务状态:" -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD ps"
    }
    
    "6" {
        Write-Host ""
        Write-Host "📋 显示应用日志 (Ctrl+C 退出):" -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD logs -f rag-server"
    }
    
    "7" {
        Write-Host ""
        Write-Host "🔧 正在初始化数据库..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD exec rag-server alembic upgrade head"
        
        Write-Host ""
        Write-Host "👤 正在创建超级管理员..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD exec rag-server python scripts/create_super_admin.py"
        
        Write-Host ""
        Write-Host "✅ 数据库初始化完成" -ForegroundColor Green
    }
    
    "8" {
        Write-Host ""
        Write-Host "🔨 正在重新构建镜像（无缓存）..." -ForegroundColor Cyan
        Invoke-Expression "$COMPOSE_CMD build --no-cache"
        
        Write-Host ""
        Write-Host "✅ 构建完成" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ 无效选项" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
