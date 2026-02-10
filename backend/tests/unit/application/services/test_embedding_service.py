"""Unit tests for embedding_service."""

from unittest.mock import AsyncMock

import pytest

from app.application.services.embedding_service import (
    CosineSimilarity,
    EmbeddingService,
)


class FakeEmbeddingClient:
    """Fake embedding client for testing."""

    def __init__(self, embedding: list[float] | None = None) -> None:
        self._embedding = embedding or [0.1, 0.2, 0.3]
        self.create_embedding = AsyncMock(return_value=self._embedding)

    @property
    def dimensions(self) -> int:
        return len(self._embedding)


class FakeEmbeddingCache:
    """Fake embedding cache for testing."""

    def __init__(self) -> None:
        self._store: dict[str, list[float]] = {}
        self.get = AsyncMock(side_effect=self._get)
        self.set = AsyncMock(side_effect=self._set)

    async def _get(self, text_hash: str) -> list[float] | None:
        return self._store.get(text_hash)

    async def _set(self, text_hash: str, embedding: list[float]) -> None:
        self._store[text_hash] = embedding


@pytest.mark.unit
class TestEmbeddingService:
    """Tests for EmbeddingService."""

    async def test_generate_returns_embedding_result(self) -> None:
        client = FakeEmbeddingClient([1.0, 2.0, 3.0])
        service = EmbeddingService(client=client)

        result = await service.generate("hello world", use_cache=False)

        assert result.embedding == [1.0, 2.0, 3.0]
        assert result.dimensions == 3
        assert result.model == "text-embedding-3-small"
        client.create_embedding.assert_called_once()

    async def test_generate_uses_cache_on_hit(self) -> None:
        client = FakeEmbeddingClient([1.0, 2.0])
        cache = FakeEmbeddingCache()
        service = EmbeddingService(client=client, cache=cache)

        # First call generates and caches
        result1 = await service.generate("test text")
        assert client.create_embedding.call_count == 1

        # Second call should use cache
        result2 = await service.generate("test text")
        assert result2.tokens_used == 0  # Cached results have 0 tokens
        assert result2.embedding == [1.0, 2.0]

    async def test_generate_without_cache(self) -> None:
        client = FakeEmbeddingClient([0.5])
        service = EmbeddingService(client=client, cache=None)

        result = await service.generate("some text")
        assert result.embedding == [0.5]

    async def test_preprocess_truncates_long_text(self) -> None:
        client = FakeEmbeddingClient()
        service = EmbeddingService(client=client, max_text_length=100)

        long_text = "x" * 200
        processed = service._preprocess_text(long_text)
        assert len(processed) < 200
        assert " ... " in processed

    async def test_generate_batch(self) -> None:
        client = FakeEmbeddingClient([0.1, 0.2])
        service = EmbeddingService(client=client)

        results = await service.generate_batch(["a", "b", "c"], use_cache=False)
        assert len(results) == 3

    async def test_dimensions_property(self) -> None:
        client = FakeEmbeddingClient([1.0, 2.0, 3.0, 4.0])
        service = EmbeddingService(client=client)
        assert service.dimensions == 4


@pytest.mark.unit
class TestCosineSimilarity:
    """Tests for CosineSimilarity."""

    def test_identical_vectors(self) -> None:
        score = CosineSimilarity.compute([1.0, 0.0], [1.0, 0.0])
        assert score == pytest.approx(1.0)

    def test_orthogonal_vectors(self) -> None:
        score = CosineSimilarity.compute([1.0, 0.0], [0.0, 1.0])
        assert score == pytest.approx(0.0)

    def test_opposite_vectors(self) -> None:
        score = CosineSimilarity.compute([1.0, 0.0], [-1.0, 0.0])
        assert score == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self) -> None:
        score = CosineSimilarity.compute([0.0, 0.0], [1.0, 0.0])
        assert score == 0.0

    def test_mismatched_dimensions_raises(self) -> None:
        with pytest.raises(ValueError, match="same dimensions"):
            CosineSimilarity.compute([1.0], [1.0, 2.0])

    def test_find_most_similar(self) -> None:
        query = [1.0, 0.0]
        embeddings = [
            (1, [1.0, 0.0]),  # Score 1.0
            (2, [0.0, 1.0]),  # Score 0.0
            (3, [0.7, 0.7]),  # Score ~0.7
        ]
        results = CosineSimilarity.find_most_similar(query, embeddings, top_k=2, min_score=0.5)
        assert len(results) == 2
        assert results[0][0] == 1  # Most similar first
        assert results[0][1] == pytest.approx(1.0)
