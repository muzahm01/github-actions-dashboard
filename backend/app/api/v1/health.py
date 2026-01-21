"""Health check endpoints."""

import logging
from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.infrastructure.database.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check() -> dict[str, str]:
    """Basic health check - always returns healthy if the app is running."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    """
    Readiness check with dependency status.

    Verifies that all required dependencies (database, Redis) are accessible.
    Returns 503 Service Unavailable if any dependency check fails.
    """
    checks = {
        "database": False,
        "redis": False,
    }

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")

    # Check Redis connectivity
    try:
        redis_client = redis.from_url(str(settings.redis_url))
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")

    # Determine overall status
    all_healthy = all(checks.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
        },
    )


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe.

    Returns alive if the application is running.
    Used by orchestrators to determine if the app needs to be restarted.
    """
    return {"status": "alive"}
