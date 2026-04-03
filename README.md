# RAG-Anything Server Project

Multi-tenant knowledge base API with RAG (Retrieval-Augmented Generation) capabilities, built on top of the RAG-Anything library.

## 🎯 Project Status

**✅ Phase 1-5 COMPLETE**: Foundation, Knowledge Base Management, and RAG Query Operations

The server provides a production-ready multi-tenant API layer for managing isolated knowledge bases with secure authentication, role-based access control, and full RAG-powered query capabilities.

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | **Start here** - Quick setup guide |
| [SERVER_README.md](SERVER_README.md) | Complete server documentation |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | What's been implemented |
| [docs/RAG_QUERY_FIX_SUMMARY.md](docs/RAG_QUERY_FIX_SUMMARY.md) | RAG query troubleshooting & fixes |
| [specs/multi-tenant-kb-api.md](C:\Users\Adam\AppData\Roaming\Lingma\SharedClientCache\cli\specs\multi-tenant-kb-api.md) | Full implementation plan |

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements-server.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 3. Run migrations
alembic upgrade head

# 4. Create admin user
python scripts/create_super_admin.py admin@example.com admin securepassword123

# 5. Start server
uvicorn server.main:app --reload

# 6. Open API docs
open http://localhost:8000/docs
```

See [GETTING_STARTED.md](GETTING_STARTED.md) for detailed instructions.

## ✨ Features

### ✅ Implemented (Phases 1-3)

- **Multi-Tenant Architecture**
  - User-as-tenant model (each user = tenant)
  - Namespace-based isolation in LightRAG storage
  - Secure tenant boundaries enforced
  - PostgreSQL + Neo4j + PGVectorStorage backend

- **Authentication & Authorization**
  - JWT tokens (30-min access + 7-day refresh)
  - API keys for programmatic access
  - Dual auth support (use either method)
  - Super admin role for cross-tenant operations

- **Knowledge Base Management**
  - Create/update/delete knowledge bases
  - Automatic namespace generation
  - Storage configuration per KB
  - Document counting and stats
  - Multi-model embedding support (Ollama/OpenAI)

- **Access Control & Collaboration**
  - Role-based permissions (owner/editor/viewer)
  - Share KBs with other users
  - Revoke access anytime
  - View all collaborators

- **RAG Query Operations** ✅ NEW
  - Naive, local, and global query modes
  - PGVectorStorage with dynamic table naming
  - LLM response caching
  - Context-aware retrieval
  - Support for multiple embedding models

- **Developer Experience**
  - Interactive Swagger UI documentation
  - Pydantic request/response validation
  - Async database operations
  - Comprehensive error handling
  - Detailed logging and debugging

### 🚧 Coming Soon (Phases 6-7)

- Rate limiting and monitoring
- Docker deployment files
- Comprehensive test suite
- Performance optimization

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌──────────┐  ┌────────────────────┐  │
│  │   Auth   │  │   Knowledge Base   │  │
│  │ Middleware│  │   Management       │  │
│  └──────────┘  └────────────────────┘  │
│            ┌──────────────────┐        │
│            │   RAG Queries    │        │
│            └──────────────────┘        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│    Multi-Tenancy Abstraction Layer      │
│  ┌──────────────────┐  ┌──────────────┐ │
│  │ User-as-Tenant   │  │ KB Metadata  │ │
│  │ (user_id=tenant) │  │ (PostgreSQL) │ │
│  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│     Enhanced RAGAnything Library        │
│  (Namespace isolation per KB)           │
│  • Dynamic model suffix generation      │
│  • Type-safe LLM wrappers               │
│  • Multi-modal processing               │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│     Storage Layer (LightRAG)            │
│  PGVector | Neo4j | PostgreSQL         │
│  • Dynamic table names with model suffix│
│  • Workspace-based isolation            │
│  • LLM response cache                   │
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
RAG-Anything-Server/
├── server/                      # FastAPI server code
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration
│   ├── schemas.py              # Pydantic models
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── database.py        # DB connection
│   │   ├── user.py            # User model
│   │   ├── knowledge_base.py  # KB model
│   │   ├── api_key.py         # API key model
│   │   └── kb_user_access.py  # Access control
│   │
│   ├── middleware/             # Authentication & tenant resolution
│   │   ├── auth.py            # JWT + API key auth
│   │   └── tenant_resolver.py # Tenant isolation
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py    # Authentication
│   │   └── kb_service.py      # KB management
│   │
│   └── routers/                # API endpoints
│       ├── auth.py            # Auth routes
│       └── knowledge_bases.py # KB CRUD routes
│
├── alembic/                    # Database migrations
│   └── versions/              # Migration scripts
│
├── scripts/                    # Utility scripts
│   └── create_super_admin.py  # Admin user creation
│
├── tests/                      # Test suite (85+ files)
│   ├── conftest.py            # Test fixtures
│   ├── test_smoke.py          # Smoke tests
│   ├── test_core_modules.py   # Core module tests
│   ├── test_callbacks.py      # Callback tests
│   ├── simple_query.py        # Query testing
│   └── test_vdb_query.py      # Vector DB tests
│
├── docs/                       # Documentation
│   ├── RAG_QUERY_FIX_SUMMARY.md  # Query troubleshooting
│   ├── batch_processing.md
│   ├── context_aware_processing.md
│   └── enhanced_markdown.md
│
├── requirements-server.txt     # Python dependencies
├── requirements.txt            # RAGAnything dependencies
├── .env.example               # Environment template
├── GETTING_STARTED.md         # Setup guide
└── TROUBLESHOOTING_SUMMARY.md # Common issues
```

## 🔑 Key Concepts

### Multi-Tenancy Model

- **User-as-Tenant**: Each user is their own tenant (simpler than separate tenant entities)
- **Namespace Isolation**: LightRAG storage namespaced as `kb_{kb_id}_{storage_type}`
- **Metadata Separation**: KB metadata in PostgreSQL, vectors in LightRAG storage
- **Super Admin**: Special role that can bypass tenant isolation

### Authentication Flow

1. **JWT Tokens** (Interactive apps):
   ```
   Login → Access Token (30m) + Refresh Token (7d)
   Use: Authorization: Bearer <token>
   ```

2. **API Keys** (Service integration):
   ```
   Create API Key → Store hash, show plain key once
   Use: X-API-Key: <key>
   ```

### RAG Query Modes

1. **Naive Mode**: Direct vector similarity search
   - Fastest query mode
   - Returns top-k most similar chunks
   - Best for factual queries

2. **Local Mode**: Entity-based retrieval
   - Uses knowledge graph entities
   - Better for relationship queries
   - Combines vector + graph search

3. **Global Mode**: Cross-entity reasoning
   - Searches across all entities
   - Best for complex, multi-hop queries
   - Most comprehensive but slower

### Access Control

- **Owner**: Full control (create/edit/delete/share)
- **Editor**: Can modify content (future feature)
- **Viewer**: Read-only access (future feature)
- **Super Admin**: Unrestricted access across all tenants

### RAG Query Modes

1. **Naive Mode**: Direct vector similarity search
   - Fastest query mode
   - Returns top-k most similar chunks
   - Best for factual queries

2. **Local Mode**: Entity-based retrieval
   - Uses knowledge graph entities
   - Better for relationship queries
   - Combines vector + graph search

3. **Global Mode**: Cross-entity reasoning
   - Searches across all entities
   - Best for complex, multi-hop queries
   - Most comprehensive but slower

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI |
| Database | PostgreSQL 14+ |
| ORM | SQLAlchemy (async) |
| Validation | Pydantic v2 |
| Auth | python-jose (JWT), passlib (bcrypt) |
| Migrations | Alembic |
| Testing | pytest, httpx |
| Rate Limiting | slowapi (ready to enable) |

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Current user info

### Knowledge Bases
- `GET /api/v1/knowledge-bases` - List KBs
- `POST /api/v1/knowledge-bases` - Create KB
- `GET /api/v1/knowledge-bases/{id}` - Get KB
- `PUT /api/v1/knowledge-bases/{id}` - Update KB
- `DELETE /api/v1/knowledge-bases/{id}` - Delete KB
- `POST /api/v1/knowledge-bases/{id}/access` - Grant access
- `GET /api/v1/knowledge-bases/{id}/users` - List collaborators

### Coming Soon
- Document upload/manage endpoints
- API key management endpoints

## 🧪 Testing

```bash
# Run smoke tests
pytest tests/test_smoke.py -v --asyncio-mode=auto

# Run all tests (85+ test files)
pytest tests/ -v --asyncio-mode=auto
```

Tests use SQLite in-memory database for speed. For production-like testing, configure a separate PostgreSQL test database in `tests/conftest.py`.

## 🔒 Security

- **Password Hashing**: bcrypt with automatic salt
- **JWT Secrets**: Environment variable (never hardcoded)
- **API Key Storage**: SHA-256 hash only (plain text shown once)
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **CORS**: Configurable allowed origins
- **Input Validation**: Pydantic schemas on all requests

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Database
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432
POSTGRES_DATABASE=raganything
POSTGRES_USER=admin
POSTGRES_PASSWORD=your-password

# LLM (Ollama example)
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:1.7b
LLM_BINDING_HOST=http://localhost:11434

# Embedding
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:0.6b

# LightRAG Storage
LIGHTRAG_KV_STORAGE=PGKVStorage
LIGHTRAG_VECTOR_STORAGE=PGVectorStorage
LIGHTRAG_GRAPH_STORAGE=Neo4JStorage
NEO4J_HOST=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### Model Support

- **Ollama** (Local, free): qwen3, llama3, mistral, etc.
- **OpenAI** (Cloud, paid): gpt-4, text-embedding-3-large
- **Custom**: Any OpenAI-compatible API

## 📈 Development Roadmap

### Phase 5: RAG Integration ✅ COMPLETE
- ✅ Enhanced RAGAnything class with tenant isolation
- ✅ Dynamic model suffix generation for vector tables
- ✅ Type-safe LLM function wrappers (single/batch support)
- ✅ PGVectorStorage integration with workspace isolation
- ✅ Multi-model embedding support (Ollama/OpenAI)
- ✅ LLM response caching for performance
- ✅ Comprehensive query testing and validation

### Phase 6: Testing (In Progress)
- ✅ Unit tests for core modules
- ✅ Integration tests for query operations
- ⏳ End-to-end document upload tests
- ⏳ Performance benchmarking
- ⏳ Error handling tests

### Phase 7: Production Readiness (Planned)
- Enable rate limiting
- Add structured logging
- Create Docker deployment files
- Monitoring and metrics
- CI/CD pipeline

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

Same as the main RAG-Anything project license.

## 🙏 Acknowledgments

Built on top of:
- [RAG-Anything](link-to-repo) - Multimodal RAG processing library
- [LightRAG](https://github.com/HKUDS/LightRAG) - Base RAG framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework

## 📞 Support

- **Documentation**: See docs folder and markdown files
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: [GitHub Issues](link-to-your-repo)

---

**Status**: ✅ Phases 1-5 Complete | 🚧 Phases 6-7 In Progress

**Latest Update**: RAG query functionality fully operational with Ollama integration, dynamic table naming, and type-safe LLM wrappers. All query modes (naive/local/global) tested and working.

For detailed setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md).

For troubleshooting RAG queries, see [docs/RAG_QUERY_FIX_SUMMARY.md](docs/RAG_QUERY_FIX_SUMMARY.md).
