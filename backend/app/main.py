"""Main FastAPI application entry point"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import make_asgi_app
from structlog import get_logger

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    SecurityHeadersMiddleware,
)

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting AI-Discover application", version=settings.VERSION)

    # Initialize database
    await init_db()

    # Initialize CrewAI agents
    logger.info("Initializing CrewAI agents")
    # TODO: Initialize agents

    yield

    # Cleanup
    logger.info("Shutting down AI-Discover application")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Health check is defined later in the file

    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # Instrument FastAPI with OpenTelemetry
    FastAPIInstrumentor.instrument_app(app)

    return app


app = create_application()


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "Welcome to AI-Discover API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint"""
    from app.core.database import get_db
    from app.core.config import settings
    import redis.asyncio as redis
    from sqlalchemy import text

    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check database connectivity
    try:
        async with get_db() as db:
            await db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = {
                "status": "healthy",
                "type": "postgresql",
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}

    # Check Redis connectivity
    try:
        redis_client = await redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = {"status": "healthy", "type": "redis"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Check if OpenAI API key is configured
    health_status["checks"]["openai"] = {
        "status": "configured" if settings.OPENAI_API_KEY else "not_configured"
    }

    return health_status
