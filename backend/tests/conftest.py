"""Pytest configuration and fixtures for backend tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User

# Test database URL - use environment variable if available (for CI)
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://testuser:testpass@localhost:5432/test_ai_discover",  # pragma: allowlist secret
)

# Override settings for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"  # pragma: allowlist secret
os.environ["REDIS_URL"] = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    # Create test engine and session for this test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# User fixtures
@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def superuser(test_db: AsyncSession) -> User:
    """Create a test superuser."""
    from app.core.security import get_password_hash
    
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_superuser=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def authenticated_client(async_client: AsyncClient, test_user: User) -> AsyncClient:
    """Create authenticated test client."""
    from app.core.security import create_access_token
    
    token = create_access_token(subject=str(test_user.id))
    async_client.headers["Authorization"] = f"Bearer {token}"
    return async_client


@pytest_asyncio.fixture
async def admin_client(async_client: AsyncClient, superuser: User) -> AsyncClient:
    """Create authenticated admin test client."""
    from app.core.security import create_access_token
    
    token = create_access_token(subject=str(superuser.id))
    async_client.headers["Authorization"] = f"Bearer {token}"
    return async_client


# Mock fixtures
@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    
    class MockCompletion:
        @staticmethod
        def create(**kwargs):
            return {
                "choices": [{
                    "message": {
                        "content": "Mocked AI response for testing"
                    }
                }]
            }
    
    class MockChatCompletions:
        create = AsyncMock(return_value=MockCompletion.create())
    
    class MockChat:
        completions = MockChatCompletions()
    
    class MockOpenAI:
        chat = MockChat()
    
    mock_client = MockOpenAI()
    monkeypatch.setattr("openai.AsyncOpenAI", lambda **kwargs: mock_client)
    return mock_client


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis operations."""
    
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
            return True
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
                return 1
            return 0
        
        async def exists(self, key):
            return key in self.data
        
        async def expire(self, key, seconds):
            return True
        
        async def ttl(self, key):
            return 3600
    
    mock = MockRedis()
    monkeypatch.setattr("app.core.cache.redis_client", mock)
    return mock


@pytest.fixture
def mock_celery_task(monkeypatch):
    """Mock Celery task execution."""
    
    class MockTask:
        def __init__(self, result=None):
            self.result = result or {"status": "completed"}
            self.id = "mock-task-id-12345"
            self.state = "SUCCESS"
        
        def delay(self, *args, **kwargs):
            return self
        
        def apply_async(self, *args, **kwargs):
            return self
        
        def get(self, timeout=None):
            return self.result
        
        @property
        def ready(self):
            return True
        
        @property
        def successful(self):
            return True
    
    return MockTask


# Test data fixtures
@pytest.fixture
def sample_discovery_request():
    """Sample discovery request data."""
    return {
        "name": "Test Discovery",
        "description": "Test application discovery",
        "target_platform": "aws",
        "source_data": {
            "region": "us-east-1",
            "account_id": "123456789012",
            "access_key": "test-access-key",
            "secret_key": "test-secret-key"
        }
    }


@pytest.fixture
def sample_application_data():
    """Sample application data."""
    return {
        "name": "Test App",
        "type": "web",
        "runtime": "python3.9",
        "framework": "fastapi",
        "dependencies": ["fastapi", "sqlalchemy", "redis"],
        "resources": {
            "cpu": "2 vCPU",
            "memory": "4 GB",
            "storage": "20 GB"
        },
        "services": ["postgresql", "redis"],
        "environment": "production"
    }


@pytest.fixture
def sample_6r_recommendations():
    """Sample 6R migration recommendations."""
    return {
        "recommendations": [
            {
                "strategy": "rehost",
                "confidence": 0.85,
                "reasoning": "Application is containerized and can be lifted and shifted",
                "effort": "low",
                "risk": "low"
            },
            {
                "strategy": "refactor",
                "confidence": 0.70,
                "reasoning": "Could benefit from cloud-native services",
                "effort": "medium",
                "risk": "medium"
            }
        ],
        "primary_recommendation": "rehost",
        "estimated_timeline": "2-4 weeks",
        "estimated_cost": "$5000-$10000"
    }


# Async utilities
@pytest.fixture
def async_mock():
    """Create an async mock factory."""
    def _create_async_mock(*args, **kwargs):
        mock = AsyncMock(*args, **kwargs)
        return mock
    return _create_async_mock
