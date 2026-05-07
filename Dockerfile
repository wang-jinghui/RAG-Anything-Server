# RAG-Anything Server Dockerfile
# 基于 Python 3.10 slim 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
# Note: MinerU API mode does NOT require LibreOffice or heavy ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    gcc \
    libxml2 \
    libxslt1.1 \
    fontconfig \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements 文件
COPY requirements-server.txt .

# 安装服务器依赖（不包括 LightRAG，它将从本地子模块安装）
RUN pip install --no-cache-dir -r requirements-server.txt

# 复制 LightRAG 子模块并离线安装（editable 模式）
COPY lightrag/ ./lightrag/
RUN cd lightrag && pip install --no-cache-dir -e .

# 复制主项目代码
COPY raganything/ ./raganything/
COPY server/ ./server/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY scripts/ ./scripts/

# 复制配置文件示例
COPY .env.example .env

# 创建必要的目录
RUN mkdir -p rag_storage temp_uploads mineru_output

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
