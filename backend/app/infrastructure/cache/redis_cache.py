"""Redis cache for error analysis and other cacheable data."""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import Settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client for caching error analyses and other data."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with settings."""
        self._redis_url = str(settings.redis_url)
        self._client: redis.Redis | None = None
        self._default_ttl = 86400 * 7  # 7 days default TTL

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute a hash for the given content."""
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            client = await self._get_client()
            serialized = json.dumps(value)
            await client.set(key, serialized, ex=ttl or self._default_ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            client = await self._get_client()
            return bool(await client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists error: {e}")
            return False

    # Specialized methods for error analysis caching

    def _analysis_key(self, log_hash: str) -> str:
        """Generate cache key for error analysis."""
        return f"analysis:{log_hash}"

    async def get_analysis(self, log_content: str) -> dict[str, Any] | None:
        """Get cached error analysis by log content hash."""
        log_hash = self.compute_hash(log_content)
        return await self.get(self._analysis_key(log_hash))

    async def set_analysis(self, log_content: str, analysis: dict[str, Any], ttl: int | None = None) -> bool:
        """Cache error analysis by log content hash."""
        log_hash = self.compute_hash(log_content)
        return await self.set(self._analysis_key(log_hash), analysis, ttl)

    async def get_analysis_by_hash(self, log_hash: str) -> dict[str, Any] | None:
        """Get cached error analysis by pre-computed hash."""
        return await self.get(self._analysis_key(log_hash))

    async def set_analysis_by_hash(
        self, log_hash: str, analysis: dict[str, Any], ttl: int | None = None
    ) -> bool:
        """Cache error analysis by pre-computed hash."""
        return await self.set(self._analysis_key(log_hash), analysis, ttl)
