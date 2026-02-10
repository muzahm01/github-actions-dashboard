"""Unit tests for search_service."""

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from app.application.services.search_service import SearchService
from app.domain.value_objects.search_query import SearchQuery, SearchType


@dataclass
class FakeEmbeddingResult:
    embedding: list[float]


class FakeLogRepo:
    """Fake log search repository."""

    def __init__(self) -> None:
        self.search_semantic = AsyncMock(return_value=[])
        self.search_text = AsyncMock(return_value=[])


class FakeEmbeddingService:
    """Fake embedding service."""

    def __init__(self) -> None:
        self.generate = AsyncMock(
            return_value=FakeEmbeddingResult(embedding=[0.1, 0.2, 0.3])
        )


@pytest.mark.unit
class TestSearchService:
    """Tests for SearchService."""

    async def test_text_search(self) -> None:
        repo = FakeLogRepo()
        repo.search_text.return_value = [
            (1, "build-job", "Error: build failed"),
            (2, "test-job", "AssertionError"),
        ]
        service = SearchService(log_repository=repo)

        query = SearchQuery(query="build failed", search_type=SearchType.TEXT, limit=10)
        response = await service.search(query)

        assert response.total == 2
        assert response.search_type == SearchType.TEXT
        assert response.results[0].id == 1
        repo.search_text.assert_called_once()

    async def test_semantic_search(self) -> None:
        repo = FakeLogRepo()
        repo.search_semantic.return_value = [
            (3, "deploy-job", "Connection refused", 0.95),
        ]
        embedding_svc = FakeEmbeddingService()
        service = SearchService(log_repository=repo, embedding_service=embedding_svc)

        query = SearchQuery(query="connection error", search_type=SearchType.SEMANTIC, limit=5)
        response = await service.search(query)

        assert response.total == 1
        assert response.search_type == SearchType.SEMANTIC
        assert response.results[0].score == 0.95
        embedding_svc.generate.assert_called_once_with("connection error")

    async def test_semantic_search_falls_back_to_text_without_embedding_service(self) -> None:
        repo = FakeLogRepo()
        repo.search_text.return_value = [(1, "job", "error text")]
        service = SearchService(log_repository=repo, embedding_service=None)

        query = SearchQuery(query="error", search_type=SearchType.SEMANTIC, limit=10)
        response = await service.search(query)

        # Should fall back to text search
        assert response.search_type == SearchType.TEXT
        repo.search_text.assert_called_once()

    async def test_hybrid_search_merges_results(self) -> None:
        repo = FakeLogRepo()
        repo.search_semantic.return_value = [
            (1, "job-a", "semantic hit", 0.9),
        ]
        repo.search_text.return_value = [
            (1, "job-a", "same log"),  # Duplicate
            (2, "job-b", "text only hit"),
        ]
        embedding_svc = FakeEmbeddingService()
        service = SearchService(log_repository=repo, embedding_service=embedding_svc)

        query = SearchQuery(query="test", search_type=SearchType.HYBRID, limit=10)
        response = await service.search(query)

        assert response.search_type == SearchType.HYBRID
        # Should deduplicate - log 1 appears only once
        ids = [r.id for r in response.results]
        assert ids.count(1) == 1
        assert 2 in ids

    async def test_find_similar_errors(self) -> None:
        repo = FakeLogRepo()
        repo.search_semantic.return_value = [
            (5, "build", "similar error", 0.85),
        ]
        embedding_svc = FakeEmbeddingService()
        service = SearchService(log_repository=repo, embedding_service=embedding_svc)

        results = await service.find_similar_errors("NullPointerException", limit=5, min_score=0.7)

        assert len(results) == 1
        assert results[0].id == 5
        assert results[0].score == 0.85

    async def test_find_similar_errors_without_embedding_service(self) -> None:
        repo = FakeLogRepo()
        service = SearchService(log_repository=repo, embedding_service=None)

        results = await service.find_similar_errors("error")
        assert results == []
