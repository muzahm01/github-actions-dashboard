"""Repository for error analyses."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.error_analysis import ErrorAnalysis
from app.infrastructure.database.repositories.base import BaseRepository


class ErrorAnalysisRepository(BaseRepository[ErrorAnalysis]):
    """Repository for managing error analysis entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, ErrorAnalysis)

    async def get_by_log_id(self, log_id: int) -> ErrorAnalysis | None:
        """Get analysis by log ID."""
        stmt = select(ErrorAnalysis).where(ErrorAnalysis.log_id == log_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent(self, limit: int = 20) -> list[ErrorAnalysis]:
        """Get recent analyses ordered by creation date."""
        stmt = (
            select(ErrorAnalysis)
            .order_by(ErrorAnalysis.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_similar_by_embedding(
        self, embedding: list[float], limit: int = 5, threshold: float = 0.7
    ) -> list[tuple[ErrorAnalysis, float]]:
        """
        Find similar analyses using vector similarity search.

        Uses cosine similarity with pgvector.
        Returns list of (ErrorAnalysis, similarity_score) tuples.
        """
        from sqlalchemy import text

        stmt = text("""
            SELECT id, 1 - (embedding <=> :embedding::vector) as similarity
            FROM error_analyses
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> :embedding::vector) >= :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """)

        result = await self._session.execute(
            stmt,
            {
                "embedding": str(embedding),
                "threshold": threshold,
                "limit": limit,
            },
        )

        rows = result.fetchall()
        analyses_with_scores = []

        for row in rows:
            analysis = await self.get_by_id(row.id)
            if analysis:
                analyses_with_scores.append((analysis, row.similarity))

        return analyses_with_scores
