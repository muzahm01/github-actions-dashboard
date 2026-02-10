"""Dashboard statistics service."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis_cache import RedisCache
from app.infrastructure.database.models.error_analysis import ErrorAnalysis
from app.infrastructure.database.models.repository import Repository
from app.infrastructure.database.models.workflow import Workflow
from app.infrastructure.database.models.workflow_run import WorkflowRun

logger = logging.getLogger(__name__)

DASHBOARD_CACHE_KEY = "dashboard:stats"
DASHBOARD_CACHE_TTL = 300  # 5 minutes


class DashboardService:
    """Service for computing dashboard statistics."""

    def __init__(
        self, session: AsyncSession, cache: RedisCache | None = None
    ) -> None:
        """Initialize with database session and optional cache."""
        self._session = session
        self._cache = cache

    async def get_stats(self) -> dict[str, Any]:
        """Compute and return dashboard statistics, with optional caching."""
        if self._cache:
            cached = await self._cache.get(DASHBOARD_CACHE_KEY)
            if cached:
                return cached

        stats = await self._compute_stats()

        if self._cache:
            await self._cache.set(DASHBOARD_CACHE_KEY, stats, ttl=DASHBOARD_CACHE_TTL)

        return stats

    async def _compute_stats(self) -> dict[str, Any]:
        """Compute dashboard statistics from the database."""
        now = datetime.now(UTC)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        repo_count = await self._count(select(func.count(Repository.id)))
        active_repo_count = await self._count(
            select(func.count(Repository.id)).where(Repository.is_active.is_(True))
        )
        workflow_count = await self._count(select(func.count(Workflow.id)))

        runs_24h = await self._count(
            select(func.count(WorkflowRun.id)).where(WorkflowRun.created_at >= last_24h)
        )
        success_24h = await self._count(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.created_at >= last_24h,
                WorkflowRun.conclusion == "success",
            )
        )
        failed_24h = await self._count(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.created_at >= last_24h,
                WorkflowRun.conclusion == "failure",
            )
        )
        success_rate_24h = (success_24h / runs_24h * 100) if runs_24h > 0 else 100.0

        runs_7d = await self._count(
            select(func.count(WorkflowRun.id)).where(WorkflowRun.created_at >= last_7d)
        )
        success_7d = await self._count(
            select(func.count(WorkflowRun.id)).where(
                WorkflowRun.created_at >= last_7d,
                WorkflowRun.conclusion == "success",
            )
        )
        success_rate_7d = (success_7d / runs_7d * 100) if runs_7d > 0 else 100.0

        analysis_count = await self._count(select(func.count(ErrorAnalysis.id)))

        avg_duration_stmt = select(func.avg(WorkflowRun.duration_seconds)).where(
            WorkflowRun.conclusion == "success",
            WorkflowRun.duration_seconds.isnot(None),
        )
        avg_duration = (await self._session.execute(avg_duration_stmt)).scalar()

        return {
            "total_repositories": repo_count,
            "active_repositories": active_repo_count,
            "total_workflows": workflow_count,
            "runs_24h": runs_24h,
            "success_24h": success_24h,
            "failed_24h": failed_24h,
            "success_rate_24h": round(success_rate_24h, 2),
            "runs_7d": runs_7d,
            "success_rate_7d": round(success_rate_7d, 2),
            "total_analyses": analysis_count,
            "avg_duration_seconds": round(avg_duration, 2) if avg_duration else None,
        }

    async def _count(self, stmt: Any) -> int:
        """Execute a count query and return the result."""
        return (await self._session.execute(stmt)).scalar() or 0
