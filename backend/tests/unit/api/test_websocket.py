"""Tests for WebSocket API endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_websocket_stats_endpoint(client):
    """Test WebSocket stats endpoint."""
    response = client.get("/api/v1/ws/stats")

    assert response.status_code == 200
    data = response.json()

    assert "active_connections" in data
    assert "status" in data
    assert isinstance(data["active_connections"], int)
    assert data["status"] in ["healthy", "no_connections"]


def test_websocket_stats_shows_zero_connections_initially(client):
    """Test that stats show zero connections initially."""
    response = client.get("/api/v1/ws/stats")

    data = response.json()
    assert data["active_connections"] == 0
    # Status is "healthy" even with 0 connections since the service is operational
    assert data["status"] == "healthy"
