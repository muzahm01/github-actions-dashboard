"""Tests for health endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.unit

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Should return healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_check_all_healthy(client: AsyncClient, mock_db_session: AsyncMock) -> None:
    """Should return ready status when all dependencies are healthy."""
    # Mock successful database query
    mock_db_session.execute = AsyncMock()

    with patch("app.api.v1.health.redis") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock()
        mock_redis_client.close = AsyncMock()
        mock_redis.from_url.return_value = mock_redis_client

        response = await client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] is True
    assert data["checks"]["redis"] is True


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient) -> None:
    """Should return alive status."""
    response = await client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_returns_checks_dict(
    client: AsyncClient, mock_db_session: AsyncMock
) -> None:
    """Should return checks dictionary with database and redis status."""
    mock_db_session.execute = AsyncMock()

    with patch("app.api.v1.health.redis") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock()
        mock_redis_client.close = AsyncMock()
        mock_redis.from_url.return_value = mock_redis_client

        response = await client.get("/health/ready")

    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
