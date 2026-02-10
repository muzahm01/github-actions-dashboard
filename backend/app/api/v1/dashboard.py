"""Dashboard API endpoints."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.dashboard_service import DashboardService
from app.config import Settings, get_settings
from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_cache(
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedisCache | None:
    """Get an optional Redis cache instance. Returns None if unavailable."""
    try:
        cache = RedisCache(settings)
        return cache
    except Exception:
        logger.debug("Redis cache unavailable, skipping cache")
        return None


@router.get("/stats")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[RedisCache | None, Depends(_get_cache)],
) -> dict[str, Any]:
    """Get dashboard statistics including run counts and success rates."""
    service = DashboardService(db, cache=cache)
    return await service.get_stats()
