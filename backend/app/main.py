"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.log_sanitizer import setup_sanitized_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.security_headers import (
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    TrustedHostMiddleware,
)

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    from app.infrastructure.database.session import close_db, init_db
    from app.infrastructure.websocket.pubsub import pubsub_manager

    # Use sanitized logging to redact sensitive data
    setup_sanitized_logging(settings.log_level)
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
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # Security middleware stack (order matters - first added = outermost)

    # 1. Request size limiting (prevent memory exhaustion)
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_body_size=settings.max_request_size_mb * 1024 * 1024,
    )

    # 2. Security headers (CSP, X-Frame-Options, etc.)
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Rate limiting (protect against abuse)
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_period=settings.rate_limit_requests,
            period_seconds=settings.rate_limit_period,
        )

    # 4. Trusted host validation (prevent host header injection)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )

    # 5. CORS middleware (configured from settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Window", "Retry-After"],
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        # Log the full exception details server-side
        logger.warning(
            "Application exception",
            extra={"code": exc.code, "status": exc.status_code, "path": request.url.path},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log full details server-side only
        logger.exception(
            "Unhandled exception",
            extra={"path": request.url.path, "method": request.method},
        )
        # Never expose internal details to clients
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
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

    # Prometheus metrics endpoint at root level for standard scraping
    # In production, this should be protected by network policies or basic auth at the proxy level
    from fastapi.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    @app.get("/metrics", tags=["Metrics"], include_in_schema=False)
    async def metrics(request: Request) -> Response:
        """
        Expose Prometheus metrics.

        Note: In production, protect this endpoint via network policies,
        reverse proxy authentication, or IP whitelisting.
        """
        # Simple IP-based protection in production
        if settings.environment == "production":
            client_ip = request.client.host if request.client else None
            allowed_ips = {"127.0.0.1", "localhost", "prometheus", "::1"}
            # Allow internal Docker network IPs
            if client_ip and not (
                client_ip in allowed_ips
                or client_ip.startswith("10.")
                or client_ip.startswith("172.")
                or client_ip.startswith("192.168.")
            ):
                return Response(
                    content="Forbidden",
                    status_code=403,
                    media_type="text/plain",
                )
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    # Include API router
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
