"""Error analysis query service."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.error_analysis import ErrorAnalysis
from app.infrastructure.database.models.log import Log
from app.infrastructure.database.repositories.error_analysis_repo import (
    ErrorAnalysisRepository,
)
from app.infrastructure.database.repositories.log_repo import LogRepository

logger = logging.getLogger(__name__)


class AnalysisQueryService:
    """Service for querying error analyses and triggering new analyses."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._log_repo = LogRepository(session)
        self._analysis_repo = ErrorAnalysisRepository(session)

    async def get_log(self, log_id: int) -> Log | None:
        """Get a log by ID."""
        return await self._log_repo.get_by_id(log_id)

    async def get_existing_analysis(self, log_id: int) -> ErrorAnalysis | None:
        """Get an existing analysis for a log."""
        return await self._analysis_repo.get_by_log_id(log_id)

    async def get_analysis_by_id(self, analysis_id: int) -> ErrorAnalysis | None:
        """Get an analysis by its ID."""
        return await self._analysis_repo.get_by_id(analysis_id)

    async def find_similar_errors(
        self, log_id: int, limit: int = 5
    ) -> dict[str, Any] | None:
        """Find similar errors for a log using vector similarity.

        Returns None if the log is not found, otherwise returns a dict
        with similar_errors list.
        """
        log = await self._log_repo.get_by_id(log_id)
        if not log:
            return None

        if not log.embedding:
            return {
                "log_id": log_id,
                "similar_errors": [],
                "message": "Log has no embedding. Generate embedding first.",
            }

        similar_logs = await self._log_repo.find_similar_by_embedding(
            embedding=log.embedding,
            limit=limit,
            threshold=0.7,
        )

        return {
            "log_id": log_id,
            "similar_errors": [
                {
                    "log_id": similar_log.id,
                    "similarity_score": round(score, 3),
                    "category": similar_log.category,
                }
                for similar_log, score in similar_logs
                if similar_log.id != log_id
            ],
        }
