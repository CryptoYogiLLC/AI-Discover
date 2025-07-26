"""DeepInfra API client for LLM integration"""

import os
from typing import Dict, List, Optional, Any
import asyncio

import httpx
from structlog import get_logger
from pydantic import BaseModel, Field


logger = get_logger(__name__)


class DeepInfraMessage(BaseModel):
    """Message format for DeepInfra API"""

    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class DeepInfraRequest(BaseModel):
    """Request format for DeepInfra API"""

    model: str = Field(default="meta-llama/Llama-4-Maverick-17B")
    messages: List[DeepInfraMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1)
    stream: bool = Field(default=False)


class DeepInfraResponse(BaseModel):
    """Response format from DeepInfra API"""

    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class DeepInfraClient:
    """Client for interacting with DeepInfra API"""

    BASE_URL = "https://api.deepinfra.com/v1/openai"
    DEFAULT_MODEL = "meta-llama/Llama-4-Maverick-17B"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize DeepInfra client

        Args:
            api_key: DeepInfra API key. If not provided, uses environment variable
        """
        self.api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DeepInfra API key not provided. Set DEEPINFRA_API_KEY environment variable."
            )

        self._client = None
        self._retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,  # seconds
            "max_delay": 60.0,  # seconds
            "exponential_base": 2,
        }

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(60.0),
            )
        return self._client

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        last_exception = None

        for attempt in range(self._retry_config["max_retries"]):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    logger.error(
                        "DeepInfra client error",
                        status_code=e.response.status_code,
                        response_text=e.response.text,
                    )
                    raise

                last_exception = e

            except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as e:
                last_exception = e

            if attempt < self._retry_config["max_retries"] - 1:
                # Calculate delay with exponential backoff
                delay = min(
                    self._retry_config["base_delay"]
                    * (self._retry_config["exponential_base"] ** attempt),
                    self._retry_config["max_delay"],
                )

                logger.warning(
                    "DeepInfra request failed, retrying",
                    attempt=attempt + 1,
                    delay=delay,
                    error=str(last_exception),
                )

                await asyncio.sleep(delay)

        logger.error(
            "DeepInfra request failed after all retries",
            retries=self._retry_config["max_retries"],
            error=str(last_exception),
        )
        raise last_exception

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
    ) -> DeepInfraResponse:
        """Send chat completion request to DeepInfra

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to Llama-4-Maverick-17B)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            DeepInfra API response
        """
        # Convert messages to DeepInfraMessage objects for validation
        validated_messages = [
            DeepInfraMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]

        request = DeepInfraRequest(
            model=model or self.DEFAULT_MODEL,
            messages=[msg.model_dump() for msg in validated_messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        logger.info(
            "Sending chat completion request",
            model=request.model,
            num_messages=len(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            response = await self._make_request_with_retry(
                "POST", "/chat/completions", json=request.model_dump()
            )

            response_data = response.json()

            logger.info(
                "Chat completion successful",
                model=request.model,
                usage=response_data.get("usage", {}),
                completion_id=response_data.get("id"),
            )

            return DeepInfraResponse(**response_data)

        except Exception as e:
            logger.error("Chat completion failed", model=request.model, error=str(e))
            raise

    async def get_completion_text(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """Get completion text from chat request

        Args:
            messages: List of message dicts
            **kwargs: Additional parameters for chat_completion

        Returns:
            Generated text content
        """
        response = await self.chat_completion(messages, **kwargs)

        if response.choices and response.choices[0].get("message"):
            return response.choices[0]["message"]["content"]

        return ""

    async def health_check(self) -> bool:
        """Check if DeepInfra API is accessible

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Send a minimal request to check connectivity
            response = await self.chat_completion(
                messages=[{"role": "user", "content": "test"}], max_tokens=1
            )
            return bool(response.id)
        except Exception as e:
            logger.error("DeepInfra health check failed", error=str(e))
            return False


# Singleton instance for convenience
_default_client: Optional[DeepInfraClient] = None


def get_deepinfra_client() -> DeepInfraClient:
    """Get default DeepInfra client instance"""
    global _default_client
    if _default_client is None:
        _default_client = DeepInfraClient()
    return _default_client
