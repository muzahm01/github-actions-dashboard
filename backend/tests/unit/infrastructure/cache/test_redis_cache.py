"""Tests for Redis cache."""

from unittest.mock import AsyncMock, patch

import pytest

from app.config import Settings
from app.infrastructure.cache.redis_cache import RedisCache


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment="testing",
        redis_url="redis://localhost:6379/0",
    )


@pytest.fixture
def redis_cache(test_settings: Settings) -> RedisCache:
    """Create Redis cache instance."""
    return RedisCache(test_settings)


class TestRedisCache:
    """Test suite for Redis cache."""

    def test_compute_hash(self, redis_cache: RedisCache) -> None:
        """Should compute consistent hash."""
        content = "test content"
        hash1 = redis_cache.compute_hash(content)
        hash2 = redis_cache.compute_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_compute_hash_different_content(self, redis_cache: RedisCache) -> None:
        """Should compute different hashes for different content."""
        hash1 = redis_cache.compute_hash("content1")
        hash2 = redis_cache.compute_hash("content2")

        assert hash1 != hash2

    def test_analysis_key_format(self, redis_cache: RedisCache) -> None:
        """Should generate correct cache key format."""
        key = redis_cache._analysis_key("abc123")
        assert key == "analysis:abc123"

    @pytest.mark.asyncio
    async def test_get_returns_none_on_error(self, redis_cache: RedisCache) -> None:
        """Should return None when Redis connection fails."""
        with patch.object(redis_cache, "_get_client", side_effect=Exception("Connection failed")):
            result = await redis_cache.get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_on_error(self, redis_cache: RedisCache) -> None:
        """Should return False when Redis set fails."""
        with patch.object(redis_cache, "_get_client", side_effect=Exception("Connection failed")):
            result = await redis_cache.set("test_key", {"data": "value"})
            assert result is False

    @pytest.mark.asyncio
    async def test_get_analysis_uses_correct_key(self, redis_cache: RedisCache) -> None:
        """Should use hash of log content as cache key."""
        log_content = "Error: Something failed"
        expected_hash = redis_cache.compute_hash(log_content)
        expected_key = f"analysis:{expected_hash}"

        mock_client = AsyncMock()
        mock_client.get.return_value = None

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            await redis_cache.get_analysis(log_content)
            mock_client.get.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_set_analysis_caches_data(self, redis_cache: RedisCache) -> None:
        """Should cache analysis data with correct key."""
        log_content = "Error: Test failure"
        analysis_data = {"root_cause": "Test error", "confidence_score": 0.9}

        mock_client = AsyncMock()
        mock_client.set.return_value = True

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.set_analysis(log_content, analysis_data)
            assert result is True
            mock_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_returns_false_on_error(self, redis_cache: RedisCache) -> None:
        """Should return False when exists check fails."""
        with patch.object(redis_cache, "_get_client", side_effect=Exception("Error")):
            result = await redis_cache.exists("test_key")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_on_error(self, redis_cache: RedisCache) -> None:
        """Should return False when delete fails."""
        with patch.object(redis_cache, "_get_client", side_effect=Exception("Error")):
            result = await redis_cache.delete("test_key")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_returns_parsed_json(self, redis_cache: RedisCache) -> None:
        """Should return parsed JSON when value exists."""
        mock_client = AsyncMock()
        mock_client.get.return_value = '{"key": "value"}'

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.get("test_key")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_missing(self, redis_cache: RedisCache) -> None:
        """Should return None when key doesn't exist."""
        mock_client = AsyncMock()
        mock_client.get.return_value = None

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.get("missing_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_serializes_and_stores(self, redis_cache: RedisCache) -> None:
        """Should serialize and store value."""
        mock_client = AsyncMock()

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.set("test_key", {"data": "value"}, ttl=3600)
            assert result is True
            mock_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, redis_cache: RedisCache) -> None:
        """Should delete key successfully."""
        mock_client = AsyncMock()

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.delete("test_key")
            assert result is True
            mock_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, redis_cache: RedisCache) -> None:
        """Should return True when key exists."""
        mock_client = AsyncMock()
        mock_client.exists.return_value = 1

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.exists("test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_missing(self, redis_cache: RedisCache) -> None:
        """Should return False when key doesn't exist."""
        mock_client = AsyncMock()
        mock_client.exists.return_value = 0

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.exists("missing_key")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_analysis_by_hash(self, redis_cache: RedisCache) -> None:
        """Should get analysis by pre-computed hash."""
        mock_client = AsyncMock()
        mock_client.get.return_value = '{"root_cause": "test"}'

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.get_analysis_by_hash("abc123")
            assert result == {"root_cause": "test"}
            mock_client.get.assert_called_once_with("analysis:abc123")

    @pytest.mark.asyncio
    async def test_set_analysis_by_hash(self, redis_cache: RedisCache) -> None:
        """Should set analysis by pre-computed hash."""
        mock_client = AsyncMock()

        with patch.object(redis_cache, "_get_client", return_value=mock_client):
            result = await redis_cache.set_analysis_by_hash(
                "abc123", {"root_cause": "test"}, ttl=3600
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_close(self, redis_cache: RedisCache) -> None:
        """Should close Redis connection."""
        mock_client = AsyncMock()
        redis_cache._client = mock_client

        await redis_cache.close()

        mock_client.close.assert_called_once()
        assert redis_cache._client is None
