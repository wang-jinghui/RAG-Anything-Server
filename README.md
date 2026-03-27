# RAG-Anything Server Project

Multi-tenant knowledge base API with RAG (Retrieval-Augmented Generation) capabilities, built on top of the RAG-Anything library.

## 🎯 Project Status

**✅ Phase 1-3 COMPLETE**: Foundation, Authentication, and Knowledge Base Management

The server provides a production-ready multi-tenant API layer for managing isolated knowledge bases with secure authentication and role-based access control.

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | **Start here** - Quick setup guide |
| [SERVER_README.md](SERVER_README.md) | Complete server documentation |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | What's been implemented |
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

- **Access Control & Collaboration**
  - Role-based permissions (owner/editor/viewer)
  - Share KBs with other users
  - Revoke access anytime
  - View all collaborators

- **Developer Experience**
  - Interactive Swagger UI documentation
  - Pydantic request/response validation
  - Async database operations
  - Comprehensive error handling

### 🚧 Coming Soon (Phases 4-7)

- Document upload and processing APIs
- RAG-powered query/search endpoints
- Integration with existing RAGAnything library
- Rate limiting and monitoring
- Docker deployment files
- Comprehensive test suite

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌──────────┐  ┌────────────────────┐  │
│  │   Auth   │  │   Knowledge Base   │  │
│  │ Middleware│  │   Management       │  │
│  └──────────┘  └────────────────────┘  │
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
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│     Storage Layer (LightRAG)            │
│  PGVector | Neo4j | PostgreSQL         │
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
├── tests/                      # Test suite
│   ├── conftest.py            # Test fixtures
│   └── test_smoke.py          # Smoke tests
│
├── requirements-server.txt     # Python dependencies
├── .env.example               # Environment template
└── GETTING_STARTED.md         # Setup guide
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

### Access Control

- **Owner**: Full control (create/edit/delete/share)
- **Editor**: Can modify content (future feature)
- **Viewer**: Read-only access (future feature)
- **Super Admin**: Unrestricted access across all tenants

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
- Query/search endpoints
- API key management endpoints

## 🧪 Testing

```bash
# Run smoke tests
pytest tests/test_smoke.py -v --asyncio-mode=auto

# Run all tests
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

## 📈 Development Roadmap

### Phase 4: Library Enhancement (Next)
- Modify RAGAnything class for tenant isolation
- Add optional `tenant_id`/`kb_id` parameters
- Implement namespace-aware LightRAG initialization

### Phase 5: Document & Query APIs
- File upload endpoints
- Connect to RAGAnything processing
- Query endpoints with tenant isolation

### Phase 6: Testing
- Unit tests for all services
- Integration tests for all endpoints
- Performance benchmarking

### Phase 7: Production Readiness
- Enable rate limiting
- Add structured logging
- Create Docker deployment files
- Monitoring and metrics

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

**Status**: ✅ Phases 1-3 Complete | 🚧 Phases 4-7 In Progress

For detailed setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md).
