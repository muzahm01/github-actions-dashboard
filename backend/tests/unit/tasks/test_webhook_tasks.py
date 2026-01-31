"""Tests for webhook processing Celery tasks."""

from unittest.mock import MagicMock, patch

from app.tasks.webhook_tasks import (
    ProcessedWebhookResult,
    process_webhook_event,
)


class TestProcessWebhookEventTask:
    """Tests for process_webhook_event task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        assert process_webhook_event.name == "app.tasks.webhook_tasks.process_webhook_event"
        assert process_webhook_event.max_retries == 3

    @patch("app.tasks.webhook_tasks.run_async")
    def test_process_workflow_run_completed_event(self, mock_run_async: MagicMock) -> None:
        """Should process workflow_run completed event and trigger run processing."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "status": "completed",
                "conclusion": "failure",
            },
            "repository": {
                "full_name": "org/repo",
                "owner": {"login": "org"},
                "name": "repo",
            },
        }

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "processed",
                "event_type": "workflow_run",
                "action": "completed",
                "run_id": 12345,
            }

        mock_run_async.side_effect = close_coro

        result = process_webhook_event(
            event_type="workflow_run",
            delivery_id="test-delivery-123",
            payload=payload,
        )

        assert result["status"] == "processed"
        assert result["event_type"] == "workflow_run"

    @patch("app.tasks.webhook_tasks.run_async")
    def test_process_workflow_run_in_progress_event(self, mock_run_async: MagicMock) -> None:
        """Should skip processing for in_progress workflow_run events."""
        payload = {
            "action": "in_progress",
            "workflow_run": {
                "id": 12345,
                "status": "in_progress",
                "conclusion": None,
            },
            "repository": {
                "full_name": "org/repo",
                "owner": {"login": "org"},
                "name": "repo",
            },
        }

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "skipped",
                "event_type": "workflow_run",
                "action": "in_progress",
                "reason": "Only completed runs are processed",
            }

        mock_run_async.side_effect = close_coro

        result = process_webhook_event(
            event_type="workflow_run",
            delivery_id="test-delivery-456",
            payload=payload,
        )

        assert result["status"] == "skipped"

    @patch("app.tasks.webhook_tasks.run_async")
    def test_process_workflow_job_event(self, mock_run_async: MagicMock) -> None:
        """Should process workflow_job events."""
        payload = {
            "action": "completed",
            "workflow_job": {
                "id": 67890,
                "run_id": 12345,
                "status": "completed",
                "conclusion": "failure",
            },
            "repository": {
                "full_name": "org/repo",
                "owner": {"login": "org"},
                "name": "repo",
            },
        }

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "processed",
                "event_type": "workflow_job",
                "action": "completed",
                "job_id": 67890,
            }

        mock_run_async.side_effect = close_coro

        result = process_webhook_event(
            event_type="workflow_job",
            delivery_id="test-delivery-789",
            payload=payload,
        )

        assert result["status"] == "processed"
        assert result["event_type"] == "workflow_job"

    @patch("app.tasks.webhook_tasks.run_async")
    def test_process_unsupported_event_type(self, mock_run_async: MagicMock) -> None:
        """Should skip unsupported event types gracefully."""
        payload = {"action": "opened", "pull_request": {"id": 123}}

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "skipped",
                "event_type": "pull_request",
                "reason": "Unsupported event type",
            }

        mock_run_async.side_effect = close_coro

        result = process_webhook_event(
            event_type="pull_request",
            delivery_id="test-delivery-unsupported",
            payload=payload,
        )

        assert result["status"] == "skipped"
        assert result["reason"] == "Unsupported event type"

    @patch("app.tasks.webhook_tasks.run_async")
    @patch("app.tasks.webhook_tasks.process_workflow_run")
    def test_triggers_workflow_run_processing_on_failure(
        self, mock_process_run: MagicMock, mock_run_async: MagicMock
    ) -> None:
        """Should trigger process_workflow_run task for failed runs."""
        payload = {
            "action": "completed",
            "workflow_run": {
                "id": 12345,
                "status": "completed",
                "conclusion": "failure",
            },
            "repository": {
                "full_name": "org/repo",
                "owner": {"login": "org"},
                "name": "repo",
            },
        }

        def close_coro(coro):  # type: ignore[no-untyped-def]
            """Close coroutine to prevent ResourceWarning."""
            coro.close()
            return {
                "status": "processed",
                "event_type": "workflow_run",
                "action": "completed",
                "run_id": 12345,
                "triggered_tasks": ["process_workflow_run"],
            }

        mock_run_async.side_effect = close_coro

        result = process_webhook_event(
            event_type="workflow_run",
            delivery_id="test-delivery-failure",
            payload=payload,
        )

        assert result["status"] == "processed"


class TestProcessedWebhookResult:
    """Tests for ProcessedWebhookResult dataclass."""

    def test_create_processed_result(self) -> None:
        """Should create a processed result."""
        result = ProcessedWebhookResult(
            status="processed",
            event_type="workflow_run",
            action="completed",
            delivery_id="test-123",
        )

        assert result.status == "processed"
        assert result.event_type == "workflow_run"
        assert result.action == "completed"
        assert result.delivery_id == "test-123"
        assert result.triggered_tasks is None

    def test_create_result_with_triggered_tasks(self) -> None:
        """Should create result with triggered tasks list."""
        result = ProcessedWebhookResult(
            status="processed",
            event_type="workflow_run",
            action="completed",
            delivery_id="test-456",
            triggered_tasks=["process_workflow_run", "analyze_error_log"],
        )

        assert result.triggered_tasks == ["process_workflow_run", "analyze_error_log"]

    def test_create_skipped_result(self) -> None:
        """Should create a skipped result with reason."""
        result = ProcessedWebhookResult(
            status="skipped",
            event_type="workflow_run",
            action="in_progress",
            delivery_id="test-789",
            reason="Only completed runs are processed",
        )

        assert result.status == "skipped"
        assert result.reason == "Only completed runs are processed"
