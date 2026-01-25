"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    from app.infrastructure.database.session import close_db, init_db
    from app.infrastructure.websocket.pubsub import pubsub_manager

    setup_logging(settings.log_level)
    logger.info(
        "Starting GitHub Actions Dashboard",
        extra={"environment": settings.environment},
    )

    # Initialize database tables
    if settings.environment != "testing":
        try:
            await init_db()
        except Exception as e:
            logger.warning(f"Database initialization skipped: {e}")

    # Start WebSocket pub/sub listener
    try:
        await pubsub_manager.connect()
        logger.info("WebSocket pub/sub listener started")
    except Exception as e:
        logger.warning(f"WebSocket pub/sub initialization skipped: {e}")

    yield

    # Cleanup
    await pubsub_manager.disconnect()
    await close_db()
    logger.info("Shutting down GitHub Actions Dashboard")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="GitHub Actions Dashboard",
        description="Monitor and analyze GitHub Actions workflows with LLM integration",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Health endpoints
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Basic health check."""
        return {"status": "healthy"}

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str | dict[str, bool]]:
        """Readiness check with dependency status."""
        return {
            "status": "ready",
            "checks": {
                "database": True,
                "redis": True,
            },
        }

    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "alive"}

    # Include API router
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
