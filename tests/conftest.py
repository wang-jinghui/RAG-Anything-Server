"""
Pytest configuration and fixtures.
"""
import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set test database URL from environment or use default
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# Set test database URL before importing server modules
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator
import asyncio

from server.models.database import Base, get_db_session
from server.main import app


# Use SQLite for simple in-memory testing (faster, no PostgreSQL needed)
# For production-like tests, use PostgreSQL test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_engine() -> AsyncGenerator:
    """Create test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables and dispose
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create FastAPI test client with overridden database dependency."""
    from fastapi.testclient import TestClient
    
    async def override_get_db_session():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepassword123"
    }


@pytest.fixture
async def authenticated_client(client, test_user_data):
    """Create authenticated test client."""
    # Register user
    register_response = client.post(
        "/api/v1/auth/register",
        json=test_user_data
    )
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    
    access_token = login_response.json()["access_token"]
    
    # Add auth header to client
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    yield client
    
    # Cleanup
    client.headers.pop("Authorization", None)
