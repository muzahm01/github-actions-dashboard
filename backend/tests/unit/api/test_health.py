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


@pytest.mark.asyncio
async def test_readiness_db_failure_returns_503() -> None:
    """Should return 503 when database is unreachable."""
    from app.api.v1.health import readiness_check
    from app.config import Settings

    session = AsyncMock()
    session.execute.side_effect = Exception("Connection refused")
    settings = Settings(
        environment="testing",
        postgres_user="t", postgres_password="t", postgres_host="localhost",
        postgres_port=5432, postgres_db="t", github_token="t",
        github_webhook_secret="s", anthropic_api_key="k", openai_api_key="k",
    )
    with patch("app.api.v1.health.redis") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock()
        mock_redis_client.close = AsyncMock()
        mock_redis.from_url.return_value = mock_redis_client

        result = await readiness_check(db=session, settings=settings)

    assert result.status_code == 503
    import json
    data = json.loads(result.body)
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] is False
    assert data["checks"]["redis"] is True


@pytest.mark.asyncio
async def test_readiness_redis_failure_returns_503() -> None:
    """Should return 503 when Redis is unreachable."""
    from app.api.v1.health import readiness_check
    from app.config import Settings

    session = AsyncMock()
    settings = Settings(
        environment="testing",
        postgres_user="t", postgres_password="t", postgres_host="localhost",
        postgres_port=5432, postgres_db="t", github_token="t",
        github_webhook_secret="s", anthropic_api_key="k", openai_api_key="k",
    )
    with patch("app.api.v1.health.redis") as mock_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock(side_effect=Exception("Connection refused"))
        mock_redis_client.close = AsyncMock()
        mock_redis.from_url.return_value = mock_redis_client

        result = await readiness_check(db=session, settings=settings)

    assert result.status_code == 503
    import json
    data = json.loads(result.body)
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] is True
    assert data["checks"]["redis"] is False


@pytest.mark.asyncio
async def test_readiness_both_fail_returns_503() -> None:
    """Should return 503 when both database and Redis fail."""
    from app.api.v1.health import readiness_check
    from app.config import Settings

    session = AsyncMock()
    session.execute.side_effect = Exception("DB down")
    settings = Settings(
        environment="testing",
        postgres_user="t", postgres_password="t", postgres_host="localhost",
        postgres_port=5432, postgres_db="t", github_token="t",
        github_webhook_secret="s", anthropic_api_key="k", openai_api_key="k",
    )
    with patch("app.api.v1.health.redis") as mock_redis:
        mock_redis.from_url.side_effect = Exception("Redis down")

        result = await readiness_check(db=session, settings=settings)

    assert result.status_code == 503
    import json
    data = json.loads(result.body)
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] is False
    assert data["checks"]["redis"] is False


@pytest.mark.asyncio
async def test_health_check_response_format(client: AsyncClient) -> None:
    """Health check should return exactly {status: healthy}."""
    response = await client.get("/health")
    data = response.json()
    assert set(data.keys()) == {"status"}


@pytest.mark.asyncio
async def test_liveness_response_format(client: AsyncClient) -> None:
    """Liveness check should return exactly {status: alive}."""
    response = await client.get("/health/live")
    data = response.json()
    assert set(data.keys()) == {"status"}
