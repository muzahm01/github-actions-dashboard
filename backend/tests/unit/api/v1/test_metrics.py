"""Tests for metrics endpoint."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1 import metrics
from app.main import app


class TestMetricsEndpoint:
    """Tests for Prometheus metrics endpoint."""

    @pytest.fixture
    def client(self) -> AsyncClient:
        """Create test client."""
        return AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        )

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_prometheus_format(
        self, client: AsyncClient
    ) -> None:
        """Test metrics endpoint returns Prometheus format."""
        async with client:
            response = await client.get("/api/v1/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # Check for some expected metrics
        content = response.text
        assert "http_requests_total" in content or "# HELP" in content


class TestMetricRecorders:
    """Tests for metric recording functions."""

    def test_record_webhook_received(self) -> None:
        """Test recording webhook received."""
        # Should not raise
        metrics.record_webhook_received("workflow_run", "success")

    def test_record_webhook_processing_time(self) -> None:
        """Test recording webhook processing time."""
        metrics.record_webhook_processing_time("workflow_run", 1.5)

    def test_record_workflow_run(self) -> None:
        """Test recording workflow run."""
        metrics.record_workflow_run("owner/repo", "CI", "success")

    def test_record_failed_job(self) -> None:
        """Test recording failed job."""
        metrics.record_failed_job("owner/repo", "test")

    def test_record_llm_request(self) -> None:
        """Test recording LLM request."""
        metrics.record_llm_request(
            provider="claude",
            operation="analyze_error",
            status="success",
            tokens=150,
            duration=2.5,
        )

    def test_record_celery_task(self) -> None:
        """Test recording Celery task."""
        metrics.record_celery_task(
            task_name="analyze_error_log",
            status="success",
            duration=5.0,
        )

    def test_set_repositories_count(self) -> None:
        """Test setting repositories count."""
        metrics.set_repositories_count(15)

    def test_set_logs_count(self) -> None:
        """Test setting logs count."""
        metrics.set_logs_count(1000)

    def test_set_embeddings_count(self) -> None:
        """Test setting embeddings count."""
        metrics.set_embeddings_count(500)
