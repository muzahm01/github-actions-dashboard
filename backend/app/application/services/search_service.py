"""Search service for semantic and text search across logs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.domain.value_objects.search_query import SearchQuery, SearchResult, SearchType

logger = logging.getLogger(__name__)


@dataclass
class SearchResponse:
    """Response from search operation."""

    results: list[SearchResult]
    total: int
    query: str
    search_type: SearchType


class LogSearchRepository(Protocol):
    """Protocol for log search operations."""

    async def search_semantic(
        self,
        embedding: list[float],
        limit: int,
        min_score: float,
        repository_ids: list[int] | None,
    ) -> list[tuple[int, str, str, float]]:
        """Search logs by embedding similarity.
        Returns: List of (log_id, job_name, content_preview, score)
        """
        ...

    async def search_text(
        self,
        query: str,
        limit: int,
        repository_ids: list[int] | None,
    ) -> list[tuple[int, str, str]]:
        """Search logs by full-text search.
        Returns: List of (log_id, job_name, content_preview)
        """
        ...


class EmbeddingService(Protocol):
    """Protocol for embedding service."""

    async def generate(self, text: str, use_cache: bool = True) -> "EmbeddingResult":
        """Generate embedding for text."""
        ...


@dataclass
class EmbeddingResult:
    """Embedding result placeholder for protocol."""

    embedding: list[float]


class SearchService:
    """Service for searching logs and error analyses."""

    def __init__(
        self,
        log_repository: LogSearchRepository,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        """Initialize search service."""
        self._log_repo = log_repository
        self._embedding_service = embedding_service

    async def search(self, query: SearchQuery) -> SearchResponse:
        """Perform search based on query type."""
        if query.search_type == SearchType.SEMANTIC:
            return await self._semantic_search(query)
        elif query.search_type == SearchType.TEXT:
            return await self._text_search(query)
        else:  # HYBRID
            return await self._hybrid_search(query)

    async def _semantic_search(self, query: SearchQuery) -> SearchResponse:
        """Perform semantic similarity search."""
        if not self._embedding_service:
            logger.warning("Embedding service not available, falling back to text search")
            return await self._text_search(query)

        # Generate embedding for query
        embedding_result = await self._embedding_service.generate(query.query)

        # Search by similarity
        results = await self._log_repo.search_semantic(
            embedding=embedding_result.embedding,
            limit=query.limit,
            min_score=query.min_score,
            repository_ids=list(query.repository_ids) if query.repository_ids else None,
        )

        # Convert to SearchResult objects
        search_results = [
            SearchResult.from_log(
                log_id=log_id,
                job_name=job_name,
                content_preview=preview,
                score=score,
            )
            for log_id, job_name, preview, score in results
        ]

        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=query.query,
            search_type=SearchType.SEMANTIC,
        )

    async def _text_search(self, query: SearchQuery) -> SearchResponse:
        """Perform full-text search."""
        results = await self._log_repo.search_text(
            query=query.query,
            limit=query.limit,
            repository_ids=list(query.repository_ids) if query.repository_ids else None,
        )

        # Convert to SearchResult objects with default score
        search_results = [
            SearchResult.from_log(
                log_id=log_id,
                job_name=job_name,
                content_preview=preview,
                score=1.0,  # Text search doesn't have similarity scores
            )
            for log_id, job_name, preview in results
        ]

        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=query.query,
            search_type=SearchType.TEXT,
        )

    async def _hybrid_search(self, query: SearchQuery) -> SearchResponse:
        """Perform hybrid search combining semantic and text results."""
        # Get results from both methods
        semantic_response = await self._semantic_search(query)
        text_response = await self._text_search(query)

        # Merge and deduplicate results
        seen_ids = set()
        merged_results = []

        # Add semantic results first (higher priority)
        for result in semantic_response.results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                merged_results.append(result)

        # Add text results
        for result in text_response.results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                # Adjust score for text results in hybrid mode
                merged_results.append(
                    SearchResult(
                        id=result.id,
                        result_type=result.result_type,
                        title=result.title,
                        description=result.description,
                        score=result.score * 0.8,  # Lower weight for text matches
                        metadata=result.metadata,
                    )
                )

        # Sort by score and limit
        merged_results.sort(key=lambda x: x.score, reverse=True)
        merged_results = merged_results[: query.limit]

        return SearchResponse(
            results=merged_results,
            total=len(merged_results),
            query=query.query,
            search_type=SearchType.HYBRID,
        )

    async def find_similar_errors(
        self,
        log_content: str,
        limit: int = 10,
        min_score: float = 0.7,
    ) -> list[SearchResult]:
        """Find similar errors based on log content."""
        if not self._embedding_service:
            logger.warning("Embedding service not available for similar error search")
            return []

        # Generate embedding for the log content
        embedding_result = await self._embedding_service.generate(log_content)

        # Search for similar logs
        results = await self._log_repo.search_semantic(
            embedding=embedding_result.embedding,
            limit=limit,
            min_score=min_score,
            repository_ids=None,
        )

        return [
            SearchResult.from_log(
                log_id=log_id,
                job_name=job_name,
                content_preview=preview,
                score=score,
            )
            for log_id, job_name, preview, score in results
        ]
