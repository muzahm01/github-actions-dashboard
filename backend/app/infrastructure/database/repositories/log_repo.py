"""Repository for logs with vector search capabilities."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import escape_like_pattern
from app.infrastructure.database.models.log import Log
from app.infrastructure.database.repositories.base import BaseRepository


class LogRepository(BaseRepository[Log]):
    """Repository for managing log entities with vector search."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, Log)

    async def get_by_job_id(self, job_id: int) -> list[Log]:
        """Get all logs for a job."""
        stmt = select(Log).where(Log.job_id == job_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_hash(self, log_hash: str) -> Log | None:
        """Get log by content hash (for deduplication)."""
        stmt = select(Log).where(Log.log_hash == log_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_logs_with_errors(self, limit: int = 50) -> list[Log]:
        """Get logs that have error content."""
        stmt = select(Log).where(Log.error_content.isnot(None)).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(self, category: str, limit: int = 50) -> list[Log]:
        """Get logs by error category."""
        stmt = select(Log).where(Log.category == category).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_similar_by_embedding(
        self, embedding: list[float], limit: int = 10, threshold: float = 0.8
    ) -> list[tuple[Log, float]]:
        """
        Find similar logs using vector similarity search.

        Uses cosine similarity with pgvector.
        Returns list of (Log, similarity_score) tuples.
        """
        # Using pgvector's cosine distance operator <=>
        # Cosine similarity = 1 - cosine_distance
        stmt = text("""
            SELECT id, 1 - (embedding <=> :embedding::vector) as similarity
            FROM logs
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
        logs_with_scores = []

        for row in rows:
            log = await self.get_by_id(row.id)
            if log:
                logs_with_scores.append((log, row.similarity))

        return logs_with_scores

    async def search_by_content(self, query: str, limit: int = 20) -> list[Log]:
        """Full-text search in log content."""
        # Escape special LIKE characters to prevent injection
        escaped_query = escape_like_pattern(query)
        # Simple ILIKE search - can be upgraded to full-text search later
        stmt = (
            select(Log)
            .where(Log.log_content.ilike(f"%{escaped_query}%", escape="\\"))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_embedding(self, log_id: int, embedding: list[float]) -> Log | None:
        """Update log's embedding vector."""
        log = await self.get_by_id(log_id)
        if log:
            log.embedding = embedding
            return await self.update(log)
        return None
