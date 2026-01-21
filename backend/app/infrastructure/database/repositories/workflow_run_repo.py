"""Repository for workflow runs."""

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.workflow_run import WorkflowRun
from app.infrastructure.database.repositories.base import BaseRepository


class WorkflowRunRepository(BaseRepository[WorkflowRun]):
    """Repository for managing workflow run entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, WorkflowRun)

    async def get_by_github_id(self, github_id: int) -> WorkflowRun | None:
        """Get workflow run by GitHub ID."""
        stmt = select(WorkflowRun).where(WorkflowRun.github_id == github_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_workflow_id(self, workflow_id: int, limit: int = 50) -> list[WorkflowRun]:
        """Get runs for a workflow, ordered by most recent."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.workflow_id == workflow_id)
            .order_by(desc(WorkflowRun.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_failures(self, limit: int = 20) -> list[WorkflowRun]:
        """Get recent failed workflow runs."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.conclusion == "failure")
            .order_by(desc(WorkflowRun.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_branch(
        self, workflow_id: int, branch: str, limit: int = 20
    ) -> list[WorkflowRun]:
        """Get runs for a specific branch."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.workflow_id == workflow_id)
            .where(WorkflowRun.head_branch == branch)
            .order_by(desc(WorkflowRun.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_jobs(self, run_id: int) -> WorkflowRun | None:
        """Get workflow run with jobs eagerly loaded."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.id == run_id)
            .options(selectinload(WorkflowRun.jobs))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_runs_in_timerange(self, start: datetime, end: datetime) -> list[WorkflowRun]:
        """Get runs within a time range."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.created_at >= start)
            .where(WorkflowRun.created_at <= end)
            .order_by(desc(WorkflowRun.created_at))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_by_github_id(self, run_data: dict) -> WorkflowRun:
        """Insert or update workflow run by GitHub ID."""
        github_id = run_data["github_id"]
        existing = await self.get_by_github_id(github_id)

        if existing:
            for key, value in run_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self.update(existing)
        else:
            run = WorkflowRun(**run_data)
            return await self.create(run)

    async def get_runs_before_date(self, cutoff_date: datetime) -> list[WorkflowRun]:
        """Get runs created before the cutoff date for cleanup."""
        stmt = (
            select(WorkflowRun)
            .where(WorkflowRun.created_at < cutoff_date)
            .options(selectinload(WorkflowRun.jobs))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
