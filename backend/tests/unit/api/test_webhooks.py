"""Tests for webhook endpoints."""
import hashlib
import hmac
import json
from typing import Any

import pytest
from httpx import AsyncClient


class TestGitHubWebhook:
    """Test suite for GitHub webhook endpoint."""

    def _generate_signature(self, payload: bytes, secret: str = "test-webhook-secret") -> str:
        """Generate valid GitHub webhook signature."""
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    @pytest.mark.asyncio
    async def test_webhook_valid_signature_accepted(
        self, client: AsyncClient, sample_workflow_run_payload: dict[str, Any]
    ) -> None:
        """Should accept webhook with valid signature."""
        payload = json.dumps(sample_workflow_run_payload).encode()
        signature = self._generate_signature(payload)

        response = await client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "workflow_run",
                "X-Hub-Signature-256": signature,
                "X-GitHub-Delivery": "test-delivery-001",
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert data["delivery_id"] == "test-delivery-001"

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_rejected(
        self, client: AsyncClient, sample_workflow_run_payload: dict[str, Any]
    ) -> None:
        """Should reject webhook with invalid signature."""
        payload = json.dumps(sample_workflow_run_payload).encode()

        response = await client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "workflow_run",
                "X-Hub-Signature-256": "sha256=invalid_signature",
                "X-GitHub-Delivery": "test-delivery-002",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_webhook_missing_headers_rejected(self, client: AsyncClient) -> None:
        """Should reject webhook with missing required headers."""
        response = await client.post(
            "/api/v1/webhooks/github",
            content=b'{"action": "completed"}',
            headers={
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 422  # Validation error for missing headers

    @pytest.mark.asyncio
    async def test_webhook_workflow_job_event(self, client: AsyncClient) -> None:
        """Should accept workflow_job event type."""
        payload = json.dumps({"action": "completed", "workflow_job": {"id": 123}}).encode()
        signature = self._generate_signature(payload)

        response = await client.post(
            "/api/v1/webhooks/github",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "workflow_job",
                "X-Hub-Signature-256": signature,
                "X-GitHub-Delivery": "test-delivery-003",
            },
        )

        assert response.status_code == 202
