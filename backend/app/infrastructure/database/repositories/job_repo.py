"""Repository for jobs."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.job import Job
from app.infrastructure.database.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Repository for managing job entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, Job)

    async def get_by_github_id(self, github_id: int) -> Job | None:
        """Get job by GitHub ID."""
        stmt = select(Job).where(Job.github_id == github_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_run_id(self, run_id: int) -> list[Job]:
        """Get all jobs for a workflow run."""
        stmt = select(Job).where(Job.run_id == run_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_jobs(self, run_id: int) -> list[Job]:
        """Get failed jobs for a run."""
        stmt = select(Job).where(Job.run_id == run_id).where(Job.conclusion == "failure")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_steps(self, job_id: int) -> Job | None:
        """Get job with steps eagerly loaded."""
        stmt = select(Job).where(Job.id == job_id).options(selectinload(Job.steps))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_logs(self, job_id: int) -> Job | None:
        """Get job with logs eagerly loaded."""
        stmt = select(Job).where(Job.id == job_id).options(selectinload(Job.logs))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_by_github_id(self, job_data: dict[str, Any]) -> Job:
        """Insert or update job by GitHub ID."""
        github_id = job_data["github_id"]
        existing = await self.get_by_github_id(github_id)

        if existing:
            for key, value in job_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self.update(existing)
        else:
            job = Job(**job_data)
            return await self.create(job)
