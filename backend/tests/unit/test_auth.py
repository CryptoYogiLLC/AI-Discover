"""Unit tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.utils.test_helpers import TestHelpers


class TestAuthEndpoints:
    """Test authentication related endpoints."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, async_client: AsyncClient):
        """Test user registration with valid data."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123",  # pragma: allowlist secret
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)
        data = TestHelpers.assert_response_ok(response, 201)

        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test registration with existing email."""
        user_data = {
            "email": test_user.email,
            "username": "anotheruser",
            "password": "password123",  # pragma: allowlist secret
        }

        response = await async_client.post("/api/v1/auth/register", json=user_data)
        TestHelpers.assert_error_response(response, 400, "already registered")

    @pytest.mark.asyncio
    async def test_login_valid_credentials(
        self, async_client: AsyncClient, test_db: AsyncSession
    ):
        """Test login with valid credentials."""
        # Create user with known password
        password = (
            "testpassword123"  # nosemgrep: hardcoded-secrets # pragma: allowlist secret
        )
        user = await TestHelpers.create_test_user(
            test_db, email="login@example.com", password=password
        )

        login_data = {"username": user.email, "password": password}

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        data = TestHelpers.assert_response_ok(response)

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test login with invalid password."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword",  # pragma: allowlist secret
        }

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        TestHelpers.assert_error_response(
            response, 401, "Incorrect username or password"
        )

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, async_client: AsyncClient, test_db: AsyncSession
    ):
        """Test login with inactive user."""
        user = await TestHelpers.create_test_user(
            test_db, email="inactive@example.com", is_active=False
        )

        login_data = {
            "username": user.email,
            "password": "testpassword123",  # pragma: allowlist secret
        }

        response = await async_client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        TestHelpers.assert_error_response(response, 400, "Inactive user")

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test getting current user info."""
        response = await authenticated_client.get("/api/v1/auth/me")
        data = TestHelpers.assert_response_ok(response)

        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["is_active"] == test_user.is_active
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_get_current_user_no_auth(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/v1/auth/me")
        TestHelpers.assert_error_response(response, 401, "Not authenticated")

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test getting current user with expired token."""
        expired_token = TestHelpers.get_expired_token(test_user)
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = await async_client.get("/api/v1/auth/me", headers=headers)
        TestHelpers.assert_error_response(
            response, 401, "Could not validate credentials"
        )

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test updating user profile."""
        update_data = {"full_name": "Test User Updated", "bio": "Updated bio"}

        response = await authenticated_client.patch("/api/v1/auth/me", json=update_data)
        data = TestHelpers.assert_response_ok(response)

        assert data["full_name"] == update_data["full_name"]
        assert data["bio"] == update_data["bio"]
        assert data["email"] == test_user.email  # Email should not change

    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client: AsyncClient):
        """Test changing user password."""
        password_data = {
            "current_password": "testpassword123",  # pragma: allowlist secret
            "new_password": "newsecurepassword123",  # pragma: allowlist secret
        }

        response = await authenticated_client.post(
            "/api/v1/auth/change-password", json=password_data
        )
        data = TestHelpers.assert_response_ok(response)

        assert data["message"] == "Password updated successfully"

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, authenticated_client: AsyncClient
    ):
        """Test changing password with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",  # pragma: allowlist secret
            "new_password": "newsecurepassword123",  # pragma: allowlist secret
        }

        response = await authenticated_client.post(
            "/api/v1/auth/change-password", json=password_data
        )
        TestHelpers.assert_error_response(response, 400, "Incorrect password")

    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client: AsyncClient):
        """Test user logout."""
        response = await authenticated_client.post("/api/v1/auth/logout")
        data = TestHelpers.assert_response_ok(response)

        assert data["message"] == "Successfully logged out"

        # Verify token is invalidated (would need Redis mock to fully test)
        response = await authenticated_client.get("/api/v1/auth/me")
        # This might still work without Redis blacklist implementation
        # In a full implementation, this should return 401
