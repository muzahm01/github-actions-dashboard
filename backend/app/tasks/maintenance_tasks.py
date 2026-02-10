"""Maintenance tasks for the GitHub Actions Dashboard."""

import asyncio
import logging
from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from app.config import get_settings
from app.infrastructure.cache.redis_cache import RedisCache
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


_T = TypeVar("_T")


def run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(soft_time_limit=60, time_limit=90)  # type: ignore[misc]
def clear_analysis_cache() -> dict[str, Any]:
    """Clear expired entries from the analysis cache."""
    logger.info("Clearing analysis cache")

    async def _clear_cache() -> dict[str, Any]:
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


@celery_app.task(soft_time_limit=60, time_limit=90)  # type: ignore[misc]
def health_check() -> dict[str, Any]:
    """Perform a health check on all system components."""
    logger.info("Running system health check")

    async def _health_check() -> dict[str, Any]:
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


@celery_app.task(soft_time_limit=300, time_limit=360)  # type: ignore[misc]
def cleanup_old_data() -> dict[str, Any]:
    """Clean up data older than the configured retention period.

    Deletes workflow runs (and cascading: jobs, logs, test results, error analyses)
    that are older than data_retention_days setting (default: 30 days).
    """
    logger.info(
        "Starting data cleanup",
        extra={"retention_days": settings.data_retention_days},
    )

    async def _cleanup() -> dict[str, Any]:
        from sqlalchemy import delete, select

        from app.infrastructure.database.models.error_analysis import ErrorAnalysis
        from app.infrastructure.database.models.job import Job
        from app.infrastructure.database.models.log import Log
        from app.infrastructure.database.models.workflow_run import WorkflowRun
        from app.infrastructure.database.session import get_session_factory

        cutoff_date = datetime.now(UTC) - timedelta(days=settings.data_retention_days)
        deleted_counts = {
            "workflow_runs": 0,
            "logs": 0,
            "error_analyses": 0,
        }

        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                # Get IDs of workflow runs to delete
                stmt = select(WorkflowRun.id).where(WorkflowRun.created_at < cutoff_date)
                result = await session.execute(stmt)
                run_ids = [row[0] for row in result.fetchall()]

                if not run_ids:
                    logger.info("No old data to clean up")
                    return {
                        "status": "completed",
                        "message": "No data older than retention period",
                        "deleted": deleted_counts,
                        "cutoff_date": cutoff_date.isoformat(),
                    }

                # Build subquery: log IDs for old runs (Log → Job → WorkflowRun)
                log_ids_subq = (
                    select(Log.id)
                    .join(Job, Log.job_id == Job.id)
                    .where(Job.run_id.in_(run_ids))
                    .scalar_subquery()
                )

                # Delete error analyses for old runs (via log_id)
                delete_analyses = delete(ErrorAnalysis).where(
                    ErrorAnalysis.log_id.in_(log_ids_subq)
                )
                analyses_result = await session.execute(delete_analyses)
                deleted_counts["error_analyses"] = analyses_result.rowcount

                # Delete logs for old runs (via job_id → run_id)
                job_ids_subq = select(Job.id).where(Job.run_id.in_(run_ids)).scalar_subquery()
                delete_logs = delete(Log).where(Log.job_id.in_(job_ids_subq))
                logs_result = await session.execute(delete_logs)
                deleted_counts["logs"] = logs_result.rowcount

                # Delete workflow runs (jobs and job_steps cascade automatically)
                delete_runs = delete(WorkflowRun).where(WorkflowRun.id.in_(run_ids))
                runs_result = await session.execute(delete_runs)
                deleted_counts["workflow_runs"] = runs_result.rowcount

                await session.commit()

                logger.info(
                    "Data cleanup completed",
                    extra={
                        "deleted": deleted_counts,
                        "cutoff_date": cutoff_date.isoformat(),
                    },
                )

                return {
                    "status": "completed",
                    "message": f"Deleted data older than {settings.data_retention_days} days",
                    "deleted": deleted_counts,
                    "cutoff_date": cutoff_date.isoformat(),
                }

            except Exception as e:
                await session.rollback()
                logger.error(f"Data cleanup failed: {e}")
                return {
                    "status": "error",
                    "message": str(e),
                    "deleted": deleted_counts,
                }

    return run_async(_cleanup())
