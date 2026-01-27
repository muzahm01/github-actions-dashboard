"""OpenAI embedding client for vector search."""

import logging

from openai import AsyncOpenAI

from app.config import Settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Client for generating text embeddings using OpenAI."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with settings."""
        self._api_key = settings.openai_api_key
        self._model = settings.openai_embedding_model
        self._dimensions = settings.openai_embedding_dimensions
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding vector for text."""
        client = self._get_client()

        # Truncate text if too long (OpenAI limit is ~8000 tokens)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]

        try:
            response = await client.embeddings.create(
                model=self._model,
                input=text,
                dimensions=self._dimensions,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise LLMError(f"OpenAI embedding error: {e}", provider="openai") from e

    async def create_embeddings_batch(
        self, texts: list[str], batch_size: int = 100
    ) -> list[list[float]]:
        """Create embeddings for multiple texts."""
        client = self._get_client()
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            # Truncate each text
            batch = [t[:30000] for t in batch]

            try:
                response = await client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.error(f"OpenAI batch embedding error: {e}")
                raise LLMError(f"OpenAI embedding error: {e}", provider="openai") from e

        return all_embeddings

    async def similarity_search_embedding(self, query: str) -> list[float]:
        """Create embedding for similarity search query."""
        # For search queries, we might want to preprocess differently
        # For now, just use the same embedding function
        return await self.create_embedding(query)

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text (alias for create_embedding)."""
        return await self.create_embedding(text)

    async def close(self) -> None:
        """Close the client connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
