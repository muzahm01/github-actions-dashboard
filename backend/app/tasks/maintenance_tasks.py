"""Maintenance tasks for the GitHub Actions Dashboard."""

import asyncio
import logging

from app.config import get_settings
from app.infrastructure.cache.redis_cache import RedisCache
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def run_async(coro):  # type: ignore[no-untyped-def]
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def clear_analysis_cache() -> dict:
    """Clear expired entries from the analysis cache."""
    logger.info("Clearing analysis cache")

    async def _clear_cache() -> dict:
        cache = RedisCache(settings)
        try:
            # Redis handles TTL automatically, but we can force-clear specific patterns if needed
            # For now, just return status since Redis auto-expires entries
            return {
                "status": "completed",
                "message": "Cache cleanup not needed - Redis handles TTL automatically",
            }
        finally:
            await cache.close()

    return run_async(_clear_cache())


@celery_app.task
def health_check() -> dict:
    """Perform a health check on all system components."""
    logger.info("Running system health check")

    async def _health_check() -> dict:
        from app.infrastructure.database.session import get_session_factory

        results = {
            "database": "unknown",
            "redis": "unknown",
            "timestamp": None,
        }

        from datetime import UTC, datetime

        results["timestamp"] = datetime.now(UTC).isoformat()

        # Check database
        try:
            session_factory = get_session_factory()
            async with session_factory() as session:
                from sqlalchemy import text

                await session.execute(text("SELECT 1"))
            results["database"] = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            results["database"] = f"unhealthy: {str(e)}"

        # Check Redis
        try:
            cache = RedisCache(settings)
            client = await cache._get_client()
            await client.ping()
            results["redis"] = "healthy"
            await cache.close()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            results["redis"] = f"unhealthy: {str(e)}"

        return results

    return run_async(_health_check())
