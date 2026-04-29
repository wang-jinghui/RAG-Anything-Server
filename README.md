# RAG-Anything Server

<div align="center">

**多租户知识库 API 服务，集成 RAG（检索增强生成）能力**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

## 🎯 项目概述

RAG-Anything Server 是一个生产级的多租户知识库 API 服务，基于 FastAPI 构建，集成了 LightRAG 和 RAG-Anything 库。它提供了完整的知识管理、文档处理、智能查询和多租户隔离功能。

### ✨ 核心特性

- **🔐 多租户架构**: 用户即租户，数据完全隔离
- **📄 智能文档处理**: 支持 PDF、DOCX、TXT、MD、PPTX、XLSX、图片等多种格式
- **🧠 RAG 查询**: 支持 naive、local、global、hybrid 等多种查询模式
- **🔑 双重认证**: JWT Token + API Key，满足不同场景需求
- **👥 协作共享**: 基于角色的访问控制（owner/editor/viewer）
- **⚡ 异步处理**: 文档上传后台异步处理，不阻塞请求
- **🌐 远程 MinerU**: 支持远程 API 调用，无需本地 GPU 依赖
- **💾 多存储后端**: PostgreSQL + Neo4j + PGVectorStorage

## 📊 系统状态

**✅ Phase 1-6 COMPLETE**: 基础架构、知识库管理、文档处理、RAG 查询全部完成

| 阶段 | 状态 | 描述 |
|------|------|------|
| Phase 1: 基础架构 | ✅ 完成 | 数据库模型、认证系统、中间件 |
| Phase 2: 知识库管理 | ✅ 完成 | CRUD 操作、命名空间隔离 |
| Phase 3: 访问控制 | ✅ 完成 | 角色权限、协作者管理 |
| Phase 4: 文档上传 | ✅ 完成 | 多格式支持、后台任务 |
| Phase 5: RAG 集成 | ✅ 完成 | LightRAG 初始化、查询接口 |
| Phase 6: 集成测试 | ✅ 完成 | 7/7 测试通过 (100%) |
| Phase 7: 生产就绪 | 🚧 进行中 | 性能优化、监控告警 |

## 🚀 快速开始

### 前置要求

- Python 3.10+
- PostgreSQL 14+ (带 pgvector 扩展)
- Neo4j 5.0+
- Ollama 或 OpenAI API（用于 LLM 和 Embedding）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/RAG-Anything-Server.git
cd RAG-Anything-Server

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements-server.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库和 LLM 服务
```

### 配置示例 (.env)

```bash
# ==========================================
# 服务器配置
# ==========================================
HOST=0.0.0.0
PORT=8000
DEBUG=true

# ==========================================
# 数据库配置
# ==========================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=raganything

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ==========================================
# JWT 认证
# ==========================================
JWT_SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==========================================
# LLM 配置 (Ollama 示例)
# ==========================================
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
LLM_BINDING_HOST=http://localhost:11434

# ==========================================
# Embedding 配置
# ==========================================
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIM=768

# ==========================================
# MinerU 解析器配置
# ==========================================
MINERU_MODE=remote  # remote 或 local
MINERU_API_TOKEN=your_mineru_api_token
MINERU_API_BASE_URL=https://mineru.net

# ==========================================
# LightRAG 存储配置
# ==========================================
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
LIGHTRAG_GRAPH_STORAGE=Neo4JStorage
LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage
```

### 启动服务

```bash
# 1. 运行数据库迁移
alembic upgrade head

# 2. 创建超级管理员账户
python scripts/create_super_admin.py admin@example.com admin securepassword123

# 3. 启动开发服务器
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# 4. 访问 API 文档
open http://localhost:8000/docs
```

## 📁 项目结构

```
RAG-Anything-Server/
├── server/                      # FastAPI 服务端代码
│   ├── main.py                 # 应用入口
│   ├── config.py               # 服务器配置
│   ├── rag_config.py           # RAG 配置
│   ├── schemas.py              # Pydantic 数据模型
│   │
│   ├── models/                 # SQLAlchemy 数据库模型
│   │   ├── database.py        # 数据库连接
│   │   ├── user.py            # 用户模型
│   │   ├── knowledge_base.py  # 知识库模型
│   │   ├── kb_document.py     # 文档模型
│   │   ├── kb_user_access.py  # 访问控制模型
│   │   └── api_key.py         # API Key 模型
│   │
│   ├── middleware/             # 中间件
│   │   ├── auth.py            # JWT + API Key 认证
│   │   └── tenant_resolver.py # 租户隔离
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── auth_service.py    # 认证服务
│   │   ├── kb_service.py      # 知识库服务
│   │   └── rag_service.py     # RAG 处理服务
│   │
│   └── routers/                # API 路由
│       ├── auth.py            # 认证接口
│       ├── knowledge_bases.py # 知识库管理
│       ├── documents.py       # 文档管理
│       └── query.py           # 查询接口
│
├── raganything/                # RAG-Anything 核心库
│   ├── raganything.py         # 主类
│   ├── config.py              # 配置管理
│   ├── parser.py              # 解析器工厂
│   ├── remote_parser.py       # 远程 MinerU 解析器
│   ├── processor.py           # 文档处理器
│   └── ...
│
├── lightrag/                   # LightRAG 子模块
│   └── lightrag/              # LightRAG 核心代码
│
├── alembic/                    # 数据库迁移
│   └── versions/              # 迁移脚本
│
├── scripts/                    # 工具脚本
│   ├── create_super_admin.py  # 创建管理员
│   └── fix_document_count.py  # 修复文档计数
│
├── demos/                      # 演示脚本
│   ├── quick_demo.py          # 快速演示
│   ├── multi_tenant_demo.py   # 多租户演示
│   ├── rag_query_demo.py      # RAG 查询演示
│   └── ...
│
├── tests/                      # 测试套件
│   ├── test_full_integration_with_upload.py  # 集成测试
│   ├── test_client_manager_multi_tenant.py   # 多租户测试
│   └── ...
│
├── docs/                       # 文档
│   ├── MULTI_TENANT_ARCHITECTURE_UPGRADE.md  # 多租户架构升级
│   ├── PHASE_6_SUCCESS_REPORT.md             # Phase 6 测试报告
│   ├── REMOTE_MINERU_INTEGRATION.md          # MinerU 远程集成
│   └── ...
│
├── requirements-server.txt     # Python 依赖
├── .env.example               # 环境变量模板
└── README.md                  # 本文件
```

## 🔑 核心概念

### 多租户模型

**用户即租户 (User-as-Tenant)**
- 每个用户拥有独立的知识库空间
- 通过 `kb_{user_id}` 命名空间实现数据隔离
- ClientManager 为每个租户维护独立的数据库连接池
- 引用计数自动管理连接生命周期

**命名空间隔离**
```python
# 每个知识库有独立的命名空间
namespace = f"kb_{kb_id}"

# LightRAG 存储表名带有命名空间前缀
chunks_vdb: "kb_{kb_id}_chunks"
entities_vdb: "kb_{kb_id}_entities"
relationships_vdb: "kb_{kb_id}_relationships"
```

### 认证与授权

**双重认证机制**

1. **JWT Token** (交互式应用)
   ```bash
   # 登录获取 Token
   POST /api/v1/auth/login
   {
     "email": "user@example.com",
     "password": "password123"
   }
   
   # 使用 Token
   Authorization: Bearer <access_token>
   ```

2. **API Key** (服务间调用)
   ```bash
   # 创建 API Key
   POST /api/v1/api-keys
   {
     "name": "My Service Key",
     "expires_in_days": 90
   }
   
   # 使用 API Key
   X-API-Key: rak_xxxxxxxxxxxx
   ```

**角色权限**
- **Owner**: 完整控制权（创建/编辑/删除/共享）
- **Editor**: 可修改内容（计划中）
- **Viewer**: 只读访问（计划中）
- **Super Admin**: 跨租户管理权限

### RAG 查询模式

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| **naive** | 直接向量相似度搜索 | 事实性查询，速度最快 |
| **local** | 基于实体的检索 | 关系型查询，结合向量+图 |
| **global** | 跨实体推理 | 复杂多跳查询，最全面 |
| **hybrid** | 混合模式（默认） | 通用场景，平衡速度与质量 |
| **mix** | 多模式组合 | 高级用法 |
| **bypass** | 绕过 RAG，直接 LLM | 不需要检索的场景 |

### 文档处理流程

```
用户上传文档
    ↓
保存临时文件
    ↓
创建数据库记录 (status: pending)
    ↓
启动后台异步任务
    ↓
立即返回响应 (202 Accepted)
    ↓
【后台处理】
    ├─ 检测文件类型
    ├─ 选择解析器 (MinerU/PaddleOCR/Direct Read)
    ├─ 解析文档内容
    ├─ 插入 LightRAG 向量库
    └─ 更新状态 (completed/failed)
```

**智能解析器路由**
```python
if file_ext in ['.md', '.txt']:
    # 直接读取文本，最高效
    selected_parser = 'direct_read'
    
elif file_ext == '.pdf':
    # 使用 MinerU (支持远程 API)
    selected_parser = 'mineru'
    
elif file_ext in ['.png', '.jpg', '.jpeg']:
    # 使用 PaddleOCR (本地 OCR)
    selected_parser = 'paddleocr'
    
else:
    # 默认使用 MinerU
    selected_parser = 'mineru'
```

## 🛠️ 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| **Web 框架** | FastAPI | 0.109.0 |
| **数据库 ORM** | SQLAlchemy (async) | 2.0.25 |
| **数据库** | PostgreSQL 14+ (pgvector) | - |
| **图数据库** | Neo4j | 5.0+ |
| **数据验证** | Pydantic v2 | 2.5.3 |
| **认证** | python-jose (JWT), passlib (bcrypt) | - |
| **数据库迁移** | Alembic | 1.13.1 |
| **测试框架** | pytest, httpx | 7.4.4, 0.26.0 |
| **RAG 引擎** | LightRAG | 1.4.11 |
| **文档解析** | MinerU, PaddleOCR, Docling | - |
| **LLM 客户端** | OpenAI SDK, Ollama | - |
| **HTTP 客户端** | aiohttp | 3.9.0+ |

## 📊 API 端点

### 认证 (`/api/v1/auth`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录 |
| POST | `/refresh` | 刷新 Token |
| GET | `/me` | 获取当前用户信息 |
| POST | `/logout` | 登出 |

### 知识库 (`/api/v1/knowledge-bases`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 列出所有知识库 |
| POST | `/` | 创建知识库 |
| GET | `/{kb_id}` | 获取知识库详情 |
| PUT | `/{kb_id}` | 更新知识库 |
| DELETE | `/{kb_id}` | 删除知识库 |
| POST | `/{kb_id}/access` | 授予访问权限 |
| DELETE | `/{kb_id}/access` | 撤销访问权限 |
| GET | `/{kb_id}/users` | 列出协作者 |

### 文档 (`/api/v1/knowledge-bases/{kb_id}/documents`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/` | 上传文档 |
| GET | `/` | 列出文档列表 |
| GET | `/{doc_id}` | 获取文档详情 |
| DELETE | `/{doc_id}` | 删除文档 |

### 查询 (`/api/v1/knowledge-bases`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/{kb_id}/query` | 查询单个知识库 |
| POST | `/query` | 跨多个知识库查询 |
| POST | `/{kb_id}/multimodal-query` | 多模态查询 |

### 健康检查

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | API 信息 |

## 🧪 测试

### 运行测试

```bash
# 运行完整集成测试
pytest tests/test_full_integration_with_upload.py -v --asyncio-mode=auto

# 运行多租户隔离测试
pytest tests/test_client_manager_multi_tenant.py -v --asyncio-mode=auto

# 运行所有测试
pytest tests/ -v --asyncio-mode=auto
```

### 测试结果

**Phase 6 集成测试**: ✅ **7/7 全部通过 (100%)**

```
✅ Server Health          - 服务器健康检查
✅ User Auth              - 用户认证
✅ Kb Creation            - 知识库创建
✅ Document Upload        - 文档上传
✅ Document Processing    - 文档后台处理
✅ Query With Docs        - 知识库查询
✅ Tenant Isolation       - 租户隔离
```

详见 [docs/PHASE_6_SUCCESS_REPORT.md](docs/PHASE_6_SUCCESS_REPORT.md)

## 🔒 安全特性

- **密码加密**: bcrypt 自动加盐哈希
- **JWT Secret**: 环境变量存储，绝不硬编码
- **API Key 存储**: 仅存储 SHA-256 哈希值
- **SQL 注入防护**: SQLAlchemy ORM 参数化查询
- **CORS 配置**: 可配置允许的来源
- **输入验证**: 所有请求使用 Pydantic 验证
- **租户隔离**: 严格的命名空间和数据访问控制

## 📈 性能优化

### 已实现的优化

1. **异步文档处理**: 后台任务不阻塞上传请求
2. **连接池管理**: ClientManager 引用计数自动清理
3. **LLM 缓存**: 可选的 LLM 响应缓存
4. **批量操作**: 文档计数批量更新

### 计划中的优化

- [ ] Redis 缓存层
- [ ] 查询结果缓存
- [ ] 增量索引更新
- [ ] 并行文档处理
- [ ] 速率限制启用
- [ ] 性能监控和告警

## 🐳 Docker 部署 (计划中)

```dockerfile
# TODO: 创建 Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY . .

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 相关文档

| 文档 | 描述 |
|------|------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | 详细入门指南 |
| [MULTI_TENANT_ARCHITECTURE_UPGRADE.md](docs/MULTI_TENANT_ARCHITECTURE_UPGRADE.md) | 多租户架构升级说明 |
| [PHASE_6_SUCCESS_REPORT.md](docs/PHASE_6_SUCCESS_REPORT.md) | Phase 6 测试报告 |
| [REMOTE_MINERU_INTEGRATION.md](docs/REMOTE_MINERU_INTEGRATION.md) | MinerU 远程 API 集成 |
| [DOCUMENT_PARSING_ARCHITECTURE.md](docs/DOCUMENT_PARSING_ARCHITECTURE.md) | 文档解析架构 |
| [RAG_CONFIGURATION_GUIDE.md](docs/RAG_CONFIGURATION_GUIDE.md) | RAG 配置指南 |

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

本项目基于以下优秀开源项目构建：

- **[RAG-Anything](https://github.com/your-org/RAG-Anything)** - 多模态 RAG 处理库
- **[LightRAG](https://github.com/HKUDS/LightRAG)** - 基础 RAG 框架
- **[FastAPI](https://fastapi.tiangolo.com/)** - 现代 Web 框架
- **[MinerU](https://github.com/opendatalab/MinerU)** - 文档解析工具

## 📞 支持与联系

- **API 文档**: http://localhost:8000/docs (运行时)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/RAG-Anything-Server/issues)
- **讨论区**: [GitHub Discussions](https://github.com/your-org/RAG-Anything-Server/discussions)

---

<div align="center">

**状态**: ✅ Phase 1-6 完成 | 🚧 Phase 7 进行中

**最后更新**: 2026-04-29

**核心功能**: 多租户隔离 · 智能文档处理 · RAG 查询 · 协作共享

</div>
