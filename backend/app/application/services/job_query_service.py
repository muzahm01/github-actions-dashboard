"""Job query service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.job import Job
from app.infrastructure.database.models.log import Log
from app.infrastructure.database.repositories.job_repo import JobRepository
from app.infrastructure.database.repositories.log_repo import LogRepository


class JobQueryService:
    """Service for querying jobs and their logs."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._job_repo = JobRepository(session)
        self._log_repo = LogRepository(session)

    async def get_job(self, job_id: int) -> Job | None:
        """Get a job by ID."""
        return await self._job_repo.get_by_id(job_id)

    async def get_job_logs(self, job_id: int) -> list[Log]:
        """Get logs for a job."""
        return await self._log_repo.get_by_job_id(job_id)
