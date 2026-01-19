"""Tests for workflow endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_workflows(client: AsyncClient) -> None:
    """Should return list of workflows."""
    response = await client.get("/api/v1/workflows/")

    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data
    assert isinstance(data["workflows"], list)


@pytest.mark.asyncio
async def test_get_workflow(client: AsyncClient) -> None:
    """Should return workflow details."""
    response = await client.get("/api/v1/workflows/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
