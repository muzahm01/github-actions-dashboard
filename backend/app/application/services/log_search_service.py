"""Log search query service."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.infrastructure.database.models.log import Log
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.external.embedding_client import EmbeddingClient

logger = logging.getLogger(__name__)


class LogSearchService:
    """Service for searching logs via semantic and text search."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Initialize with database session and settings."""
        self._log_repo = LogRepository(session)
        self._settings = settings

    async def semantic_search(
        self, query: str, limit: int = 10
    ) -> dict[str, Any]:
        """Perform semantic search using embeddings."""
        embedding_client = EmbeddingClient(self._settings)
        try:
            query_embedding = await embedding_client.generate_embedding(query)
        except Exception as e:
            logger.error("Failed to generate embedding for search", exc_info=e)
            return {
                "query": query,
                "results": [],
                "error": "Failed to generate embedding. Please try again later.",
            }
        finally:
            await embedding_client.close()

        similar_logs = await self._log_repo.find_similar_by_embedding(
            embedding=query_embedding,
            limit=limit,
            threshold=0.6,
        )

        return {
            "query": query,
            "results": [
                {
                    "log_id": log.id,
                    "job_id": log.job_id,
                    "similarity_score": round(score, 3),
                    "category": log.category,
                    "preview": (log.log_content[:200] + "...")
                    if log.log_content and len(log.log_content) > 200
                    else log.log_content,
                }
                for log, score in similar_logs
            ],
            "total": len(similar_logs),
        }

    async def text_search(self, query: str, limit: int = 10) -> list[Log]:
        """Perform text search in log content."""
        return await self._log_repo.search_by_content(query=query, limit=limit)

    async def search_logs(
        self,
        query: str = "",
        category: str | None = None,
        limit: int = 20,
    ) -> list[Log]:
        """Search logs with optional filters."""
        if category:
            return await self._log_repo.get_by_category(category, limit=limit)
        elif query:
            return await self._log_repo.search_by_content(query, limit=limit)
        return await self._log_repo.get_logs_with_errors(limit=limit)
