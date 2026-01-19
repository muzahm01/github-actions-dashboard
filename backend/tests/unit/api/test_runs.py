"""Tests for workflow run endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_runs(client: AsyncClient) -> None:
    """Should return list of runs."""
    response = await client.get("/api/v1/runs/")

    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert isinstance(data["runs"], list)


@pytest.mark.asyncio
async def test_get_run(client: AsyncClient) -> None:
    """Should return run details."""
    response = await client.get("/api/v1/runs/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
