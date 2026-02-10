"""Workflow run query service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.workflow_run import WorkflowRun
from app.infrastructure.database.repositories.workflow_run_repo import WorkflowRunRepository


class WorkflowRunQueryService:
    """Service for querying workflow runs."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._repo = WorkflowRunRepository(session)

    async def list_runs(
        self,
        limit: int = 20,
        offset: int = 0,
        conclusion: str | None = None,
    ) -> tuple[list[WorkflowRun], int]:
        """List runs with optional filtering. Returns (runs, total_count)."""
        if conclusion == "failure":
            runs = await self._repo.get_recent_failures(limit=limit)
            return runs, len(runs)
        runs = await self._repo.get_all(limit=limit, offset=offset)
        total = await self._repo.count()
        return runs, total

    async def get_recent_failures(self, limit: int = 10) -> list[WorkflowRun]:
        """Get recent failed workflow runs."""
        return await self._repo.get_recent_failures(limit=limit)

    async def get_run_with_jobs(self, run_id: int) -> WorkflowRun | None:
        """Get a workflow run with its jobs eagerly loaded."""
        return await self._repo.get_with_jobs(run_id)
