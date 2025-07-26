"""Test helper utilities for backend tests."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import MagicMock

from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


class TestHelpers:
    """Collection of test helper methods."""
    
    @staticmethod
    async def create_test_user(
        db: AsyncSession,
        email: str = "test@example.com",
        username: str = "testuser",
        password: str = "testpassword123",
        is_active: bool = True,
        is_superuser: bool = False
    ) -> User:
        """Create a test user with custom attributes."""
        from app.core.security import get_password_hash
        
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            is_active=is_active,
            is_superuser=is_superuser,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    def get_auth_headers(user: User) -> Dict[str, str]:
        """Get authorization headers for a user."""
        token = create_access_token(subject=str(user.id))
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def get_expired_token(user: User) -> str:
        """Create an expired JWT token for testing."""
        expires_delta = timedelta(minutes=-30)  # Expired 30 minutes ago
        return create_access_token(subject=str(user.id), expires_delta=expires_delta)
    
    @staticmethod
    def assert_response_ok(response: Response, status_code: int = 200) -> Dict[str, Any]:
        """Assert response is successful and return JSON data."""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
        return response.json()
    
    @staticmethod
    def assert_error_response(response: Response, status_code: int, detail: str = None):
        """Assert response is an error with optional detail check."""
        assert response.status_code == status_code
        data = response.json()
        assert "detail" in data
        if detail:
            assert detail in data["detail"]
    
    @staticmethod
    def mock_successful_discovery():
        """Create a mock successful discovery result."""
        return {
            "id": "discovery-123",
            "status": "completed",
            "applications": [
                {
                    "name": "app1",
                    "type": "web",
                    "runtime": "python3.9",
                    "recommendation": "rehost"
                }
            ],
            "summary": {
                "total_applications": 1,
                "migration_complexity": "low"
            }
        }
    
    @staticmethod
    def mock_crewai_agent_response():
        """Mock a CrewAI agent response."""
        return MagicMock(
            raw=json.dumps({
                "analysis": "Application analysis complete",
                "recommendations": {
                    "primary": "rehost",
                    "alternatives": ["refactor", "replatform"]
                },
                "confidence": 0.85
            })
        )
    
    @staticmethod
    def assert_pagination(data: Dict[str, Any], expected_total: int = None):
        """Assert pagination response structure."""
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        
        if expected_total is not None:
            assert data["total"] == expected_total
    
    @staticmethod
    def compare_datetime(dt1: datetime, dt2: datetime, tolerance_seconds: int = 5) -> bool:
        """Compare two datetimes with tolerance."""
        if dt1 is None or dt2 is None:
            return dt1 == dt2
        
        diff = abs((dt1 - dt2).total_seconds())
        return diff <= tolerance_seconds


class AsyncContextManager:
    """Helper for creating async context managers in tests."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def create_mock_redis_client():
    """Create a mock Redis client for testing."""
    class MockRedisClient:
        def __init__(self):
            self.data = {}
            self.expiry = {}
        
        async def get(self, key: str) -> str | None:
            if key in self.expiry:
                if datetime.utcnow() > self.expiry[key]:
                    del self.data[key]
                    del self.expiry[key]
                    return None
            return self.data.get(key)
        
        async def set(self, key: str, value: str, ex: int = None) -> bool:
            self.data[key] = value
            if ex:
                self.expiry[key] = datetime.utcnow() + timedelta(seconds=ex)
            return True
        
        async def delete(self, key: str) -> int:
            deleted = 0
            if key in self.data:
                del self.data[key]
                deleted = 1
            if key in self.expiry:
                del self.expiry[key]
            return deleted
        
        async def exists(self, key: str) -> bool:
            return key in self.data
        
        async def expire(self, key: str, seconds: int) -> bool:
            if key in self.data:
                self.expiry[key] = datetime.utcnow() + timedelta(seconds=seconds)
                return True
            return False
        
        async def ttl(self, key: str) -> int:
            if key not in self.expiry:
                return -1
            
            remaining = (self.expiry[key] - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
        
        def pipeline(self):
            return self
        
        async def execute(self):
            return []
    
    return MockRedisClient()


def create_mock_celery_app():
    """Create a mock Celery app for testing."""
    class MockCeleryApp:
        def __init__(self):
            self.tasks = {}
        
        def task(self, *args, **kwargs):
            def decorator(func):
                task_name = kwargs.get("name", func.__name__)
                
                class MockTask:
                    def __init__(self):
                        self.name = task_name
                        self.func = func
                    
                    def delay(self, *args, **kwargs):
                        return MockAsyncResult(func(*args, **kwargs))
                    
                    def apply_async(self, args=None, kwargs=None, **options):
                        result = func(*(args or []), **(kwargs or {}))
                        return MockAsyncResult(result)
                
                mock_task = MockTask()
                self.tasks[task_name] = mock_task
                return mock_task
            
            return decorator
    
    class MockAsyncResult:
        def __init__(self, result):
            self.result = result
            self.id = f"mock-task-{datetime.utcnow().timestamp()}"
            self.state = "SUCCESS"
        
        def get(self, timeout=None):
            return self.result
        
        @property
        def ready(self):
            return True
        
        @property
        def successful(self):
            return True
        
        @property
        def failed(self):
            return False
    
    return MockCeleryApp()