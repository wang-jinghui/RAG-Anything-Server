# RAG-Anything Server 演示脚本目录

本目录包含 RAG-Anything Server 的完整功能演示脚本。

## 📁 文件结构

```
demos/
├── README.md                      # 本文件 - 演示说明文档
├── full_demo.py                   # 完整功能演示（45-50 分钟）
├── quick_demo.py                  # 快速演示（10-15 分钟）
├── multi_tenant_demo.py           # 多租户隔离演示（20 分钟）
├── rag_query_demo.py              # RAG 查询功能演示（15 分钟）
└── cleanup_demo.py                # 清理演示数据脚本
```

## 🎯 演示脚本列表

### 1. full_demo.py - 完整功能演示
**时长**: 45-50 分钟  
**覆盖内容**:
- ✅ 系统初始化与认证
- ✅ 多租户演示（用户 A + 用户 B）
- ✅ 知识共享与协作
- ✅ API Key 管理
- ✅ 三种查询模式对比
- ✅ 监控与调试

**适用场景**: 全面技术展示、客户演示、团队培训

---

### 2. quick_demo.py - 快速演示
**时长**: 10-15 分钟  
**覆盖内容**:
- ✅ 快速用户注册与登录
- ✅ 创建单个知识库
- ✅ 上传 1-2 个文档
- ✅ 执行 RAG 查询
- ✅ 展示查询结果

**适用场景**: 快速验证、会议演示、时间受限场景

---

### 3. multi_tenant_demo.py - 多租户隔离演示
**时长**: 20 分钟  
**覆盖内容**:
- ✅ 创建多个租户
- ✅ 租户间数据隔离验证
- ✅ 跨租户查询对比
- ✅ 权限控制展示

**适用场景**: 安全性演示、多租户架构说明

---

### 4. rag_query_demo.py - RAG 查询功能演示
**时长**: 15 分钟  
**覆盖内容**:
- ✅ Naive 模式查询
- ✅ Local 模式查询
- ✅ Global 模式查询
- ✅ 三种模式对比分析

**适用场景**: 技术深度演示、研发团队分享

---

### 5. cleanup_demo.py - 清理脚本
**用途**: 清理演示过程中创建的测试数据
- 删除测试用户
- 删除测试知识库
- 清理向量数据库
- 重置 workspace

---

## 🚀 快速开始

### 前置条件检查

运行任何演示脚本前，请确保：

```bash
# 1. PostgreSQL 运行中
# 2. Neo4j 运行中（如使用）
# 3. Ollama 服务可用
# 4. 虚拟环境已激活
# 5. 依赖已安装
pip install -r requirements-server.txt
```

### 运行完整演示

```bash
# 方式 1: 直接运行完整演示
python demos/full_demo.py

# 方式 2: 分步骤运行
python demos/quick_demo.py          # 先运行快速演示
python demos/multi_tenant_demo.py   # 再运行多租户演示
python demos/rag_query_demo.py      # 最后运行查询演示
```

### 清理演示数据

```bash
python demos/cleanup_demo.py
```

---

## 📋 演示大纲详情

每个演示脚本都遵循以下结构：

### 阶段 1：系统初始化 (5 分钟)
- 启动服务器
- 创建管理员
- 验证 API 文档

### 阶段 2：用户与认证 (5 分钟)
- 注册用户
- 获取 JWT Token
- 验证认证机制

### 阶段 3：知识库管理 (10 分钟)
- 创建知识库
- 验证命名空间隔离
- 查看知识库列表

### 阶段 4：文档处理 (10 分钟)
- 上传文档
- 等待处理完成
- 查看处理统计

### 阶段 5：RAG 查询 (10 分钟)
- 执行查询
- 对比不同模式
- 展示检索结果

### 阶段 6：高级功能 (10 分钟，可选)
- API Key 管理
- 知识共享
- 权限控制

---

## ⚠️ 注意事项

### 1. 环境配置
确保 `.env` 文件正确配置：
```bash
POSTGRES_HOST=your-db-host
POSTGRES_DATABASE=raganything
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:1.7b
EMBEDDING_MODEL=qwen3-embedding:0.6b
```

### 2. 演示数据
- 演示会创建真实的测试用户和知识库
- 建议在生产环境外运行
- 运行后使用 `cleanup_demo.py` 清理

### 3. 性能考虑
- 完整演示约需 10-15 分钟实际运行时间
- 文档处理时间取决于文件大小和数量
- 查询响应时间取决于 LLM 服务

### 4. 故障排除
如遇问题，检查：
- 数据库连接日志
- 服务器控制台输出
- Ollama 服务状态

---

## 🎓 学习路径

### 第一次接触
1. 阅读 `README.md`
2. 运行 `quick_demo.py`
3. 查看 API 文档 http://localhost:8000/docs

### 深入了解
1. 运行 `full_demo.py`
2. 阅读源码了解实现细节
3. 尝试修改参数观察效果

### 高级使用
1. 运行 `multi_tenant_demo.py`
2. 运行 `rag_query_demo.py`
3. 基于演示脚本开发自定义功能

---

## 📞 支持

- **API 文档**: http://localhost:8000/docs
- **问题反馈**: GitHub Issues
- **技术讨论**: GitHub Discussions

---

## 📝 版本历史

- **v1.0** (2026-04-03): 初始版本
  - 完整的演示脚本框架
  - 5 个核心演示脚本
  - 详细的文档说明
