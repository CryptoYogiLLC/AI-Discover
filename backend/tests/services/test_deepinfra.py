"""Tests for DeepInfra API client"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.deepinfra import (
    DeepInfraClient,
    DeepInfraMessage,
    DeepInfraRequest,
    DeepInfraResponse,
    get_deepinfra_client,
)


@pytest.fixture
def mock_api_key():
    """Mock API key for testing"""
    return "test-api-key-123"


@pytest.fixture
def deepinfra_client(mock_api_key):
    """Create DeepInfra client instance for testing"""
    return DeepInfraClient(api_key=mock_api_key)


@pytest.fixture
def mock_chat_response():
    """Mock chat completion response"""
    return {
        "id": "chat-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "meta-llama/Llama-4-Maverick-17B",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "This is a test response"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


class TestDeepInfraClient:
    """Test DeepInfra client functionality"""

    def test_client_initialization_with_api_key(self, mock_api_key):
        """Test client initialization with provided API key"""
        client = DeepInfraClient(api_key=mock_api_key)
        assert client.api_key == mock_api_key

    def test_client_initialization_from_env(self, monkeypatch, mock_api_key):
        """Test client initialization from environment variable"""
        monkeypatch.setenv("DEEPINFRA_API_KEY", mock_api_key)
        client = DeepInfraClient()
        assert client.api_key == mock_api_key

    def test_client_initialization_no_api_key(self):
        """Test client initialization fails without API key"""
        with pytest.raises(ValueError, match="DeepInfra API key not provided"):
            DeepInfraClient(api_key=None)

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, deepinfra_client, mock_chat_response):
        """Test successful chat completion request"""
        with patch.object(
            deepinfra_client, "_make_request_with_retry", new_callable=AsyncMock
        ) as mock_request:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_chat_response
            mock_request.return_value = mock_response

            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
            ]

            response = await deepinfra_client.chat_completion(messages)

            assert isinstance(response, DeepInfraResponse)
            assert response.id == "chat-123"
            assert response.model == "meta-llama/Llama-4-Maverick-17B"
            assert len(response.choices) == 1
            assert (
                response.choices[0]["message"]["content"] == "This is a test response"
            )

    @pytest.mark.asyncio
    async def test_get_completion_text(self, deepinfra_client, mock_chat_response):
        """Test getting completion text from response"""
        with patch.object(
            deepinfra_client, "chat_completion", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = DeepInfraResponse(**mock_chat_response)

            messages = [{"role": "user", "content": "Hello"}]
            text = await deepinfra_client.get_completion_text(messages)

            assert text == "This is a test response"

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, deepinfra_client):
        """Test retry mechanism on server errors"""
        with patch.object(
            deepinfra_client.client, "request", new_callable=AsyncMock
        ) as mock_request:
            # First two attempts fail with server error, third succeeds
            mock_request.side_effect = [
                httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500, text="Internal error"),
                ),
                httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=MagicMock(status_code=503, text="Service unavailable"),
                ),
                MagicMock(
                    status_code=200,
                    json=lambda: {"id": "success"},
                    raise_for_status=lambda: None,
                ),
            ]

            response = await deepinfra_client._make_request_with_retry("POST", "/test")

            assert mock_request.call_count == 3
            assert response.json()["id"] == "success"

    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self, deepinfra_client):
        """Test no retry on client errors (4xx)"""
        with patch.object(
            deepinfra_client.client, "request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "Bad request",
                request=MagicMock(),
                response=MagicMock(status_code=400, text="Invalid request"),
            )

            with pytest.raises(httpx.HTTPStatusError):
                await deepinfra_client._make_request_with_retry("POST", "/test")

            # Should not retry on client error
            assert mock_request.call_count == 1

    @pytest.mark.asyncio
    async def test_health_check_success(self, deepinfra_client, mock_chat_response):
        """Test health check when API is accessible"""
        with patch.object(
            deepinfra_client, "chat_completion", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.return_value = DeepInfraResponse(**mock_chat_response)

            is_healthy = await deepinfra_client.health_check()
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, deepinfra_client):
        """Test health check when API is not accessible"""
        with patch.object(
            deepinfra_client, "chat_completion", new_callable=AsyncMock
        ) as mock_chat:
            mock_chat.side_effect = Exception("Connection failed")

            is_healthy = await deepinfra_client.health_check()
            assert is_healthy is False

    @pytest.mark.asyncio
    async def test_context_manager(self, deepinfra_client):
        """Test async context manager functionality"""
        async with deepinfra_client as client:
            assert client is deepinfra_client
            assert client._client is not None

        # Client should be closed after exiting context
        assert deepinfra_client._client is None

    def test_message_validation(self):
        """Test message format validation"""
        # Valid message
        msg = DeepInfraMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

        # Invalid role should raise validation error
        with pytest.raises(Exception):
            DeepInfraMessage(role="invalid", content="Hello")

    def test_request_validation(self):
        """Test request format validation"""
        messages = [DeepInfraMessage(role="user", content="Hello")]

        request = DeepInfraRequest(
            messages=[msg.model_dump() for msg in messages],
            temperature=1.5,
            max_tokens=500,
        )

        assert request.model == "meta-llama/Llama-4-Maverick-17B"
        assert request.temperature == 1.5
        assert request.max_tokens == 500
        assert not request.stream

    def test_get_deepinfra_client_singleton(self, monkeypatch, mock_api_key):
        """Test singleton client instance"""
        monkeypatch.setenv("DEEPINFRA_API_KEY", mock_api_key)

        # Clear any existing singleton
        import app.services.deepinfra

        app.services.deepinfra._default_client = None

        client1 = get_deepinfra_client()
        client2 = get_deepinfra_client()

        assert client1 is client2
