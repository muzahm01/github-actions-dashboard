"""Embedding service for generating and managing vector embeddings."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingRequest:
    """Request for generating embedding."""

    text: str
    model: str = "text-embedding-3-small"


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embedding: list[float]
    model: str
    dimensions: int
    tokens_used: int
    text_hash: str


class EmbeddingClient(Protocol):
    """Protocol for embedding generation client."""

    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding for text."""
        ...

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        ...


class EmbeddingCache(Protocol):
    """Protocol for embedding cache."""

    async def get(self, text_hash: str) -> list[float] | None:
        """Get cached embedding."""
        ...

    async def set(self, text_hash: str, embedding: list[float]) -> None:
        """Cache embedding."""
        ...


class EmbeddingService:
    """Service for generating and managing embeddings."""

    def __init__(
        self,
        client: EmbeddingClient,
        cache: EmbeddingCache | None = None,
        max_text_length: int = 8000,
    ) -> None:
        """Initialize embedding service."""
        self._client = client
        self._cache = cache
        self._max_text_length = max_text_length
        self._model = "text-embedding-3-small"

    async def generate(self, text: str, use_cache: bool = True) -> EmbeddingResult:
        """Generate embedding for text."""
        # Truncate text if needed
        processed_text = self._preprocess_text(text)
        text_hash = self._compute_hash(processed_text)

        # Check cache
        if use_cache and self._cache:
            cached = await self._cache.get(text_hash)
            if cached:
                logger.debug("Returning cached embedding", extra={"hash": text_hash[:8]})
                return EmbeddingResult(
                    embedding=cached,
                    model=self._model,
                    dimensions=len(cached),
                    tokens_used=0,
                    text_hash=text_hash,
                )

        # Generate embedding
        logger.debug("Generating new embedding", extra={"text_length": len(processed_text)})
        embedding = await self._client.create_embedding(processed_text)

        # Cache result
        if self._cache:
            await self._cache.set(text_hash, embedding)

        return EmbeddingResult(
            embedding=embedding,
            model=self._model,
            dimensions=len(embedding),
            tokens_used=len(processed_text) // 4,  # Approximate token count
            text_hash=text_hash,
        )

    async def generate_batch(
        self,
        texts: list[str],
        use_cache: bool = True,
        max_concurrent: int = 10,
    ) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(text: str) -> EmbeddingResult:
            async with semaphore:
                return await self.generate(text, use_cache=use_cache)

        results = await asyncio.gather(
            *[generate_with_semaphore(text) for text in texts],
            return_exceptions=True,
        )

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch embedding failed for text {i}: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding generation."""
        # Remove excessive whitespace
        import re

        text = re.sub(r"\s+", " ", text).strip()

        # Truncate if needed
        if len(text) > self._max_text_length:
            # Keep beginning and end for context
            half = self._max_text_length // 2
            text = text[:half] + " ... " + text[-half:]

        return text

    def _compute_hash(self, text: str) -> str:
        """Compute hash for text."""
        return hashlib.sha256(text.encode()).hexdigest()

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        return self._client.dimensions


class CosineSimilarity:
    """Utility for computing cosine similarity between embeddings."""

    @staticmethod
    def compute(embedding1: list[float], embedding2: list[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have same dimensions")

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    @staticmethod
    def find_most_similar(
        query_embedding: list[float],
        embeddings: list[tuple[int, list[float]]],
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> list[tuple[int, float]]:
        """Find most similar embeddings to query.

        Args:
            query_embedding: Query embedding vector
            embeddings: List of (id, embedding) tuples
            top_k: Number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of (id, score) tuples sorted by score descending
        """
        scores = []
        for item_id, embedding in embeddings:
            score = CosineSimilarity.compute(query_embedding, embedding)
            if score >= min_score:
                scores.append((item_id, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
