"""Repository for test results."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.test_result import TestResult
from app.infrastructure.database.repositories.base import BaseRepository


class TestResultRepository(BaseRepository[TestResult]):
    """Repository for managing test result entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, TestResult)

    async def get_by_log_id(self, log_id: int, limit: int = 100, offset: int = 0) -> list[TestResult]:
        """Get all test results for a log."""
        stmt = (
            select(TestResult)
            .where(TestResult.log_id == log_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_framework(self, framework: str, limit: int = 50) -> list[TestResult]:
        """Get test results by framework."""
        stmt = select(TestResult).where(TestResult.framework == framework).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_tests(self, limit: int = 50) -> list[TestResult]:
        """Get test results with failures."""
        stmt = select(TestResult).where(TestResult.failed > 0).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 20) -> list[TestResult]:
        """Get recent test results ordered by creation date."""
        stmt = select(TestResult).order_by(TestResult.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
