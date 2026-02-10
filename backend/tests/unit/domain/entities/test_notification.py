"""Tests for Notification domain entity."""

import pytest

from app.domain.entities.notification import (
    DailySummaryPayload,
    Notification,
    NotificationChannel,
    NotificationConfig,
    NotificationType,
    WorkflowFailedPayload,
)


class TestNotification:
    """Tests for the Notification entity."""

    @pytest.mark.unit
    def test_create(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="Build Failed",
            message="CI build failed on main",
        )
        assert n.id == 0
        assert n.status == "pending"
        assert n.notification_type == NotificationType.WORKFLOW_FAILED
        assert n.channel == NotificationChannel.SLACK
        assert n.retry_count == 0

    @pytest.mark.unit
    def test_create_with_metadata(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.DAILY_SUMMARY,
            channel=NotificationChannel.DISCORD,
            title="Summary",
            message="Daily report",
            metadata={"total_runs": 42},
        )
        assert n.metadata == {"total_runs": 42}

    @pytest.mark.unit
    def test_create_no_metadata(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="t",
            message="m",
        )
        assert n.metadata == {}

    @pytest.mark.unit
    def test_mark_sent(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="t",
            message="m",
        )
        n.mark_sent()
        assert n.status == "sent"
        assert n.sent_at is not None
        assert n.is_sent() is True

    @pytest.mark.unit
    def test_mark_failed_retries(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="t",
            message="m",
        )
        n.mark_failed()
        assert n.status == "retrying"
        assert n.retry_count == 1

    @pytest.mark.unit
    def test_mark_failed_exhausted(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="t",
            message="m",
        )
        # max_retries=3: mark_failed increments retry_count while < max_retries
        n.mark_failed()  # retry_count=1, status="retrying"
        n.mark_failed()  # retry_count=2, status="retrying"
        n.mark_failed()  # retry_count=3, status="retrying"
        assert n.can_retry() is False
        n.mark_failed()  # retry_count=3 (not < 3), status="failed"
        assert n.status == "failed"

    @pytest.mark.unit
    def test_can_retry(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="t",
            message="m",
        )
        assert n.can_retry() is True
        n.mark_failed()
        n.mark_failed()
        n.mark_failed()
        assert n.can_retry() is False

    @pytest.mark.unit
    def test_is_sent_false_when_pending(self) -> None:
        n = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="t",
            message="m",
        )
        assert n.is_sent() is False


class TestNotificationConfig:
    """Tests for NotificationConfig."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        config = NotificationConfig(channel=NotificationChannel.SLACK)
        assert config.enabled is True
        assert config.webhook_url == ""
        assert config.events == []
        assert config.repository_filter == []

    @pytest.mark.unit
    def test_with_values(self) -> None:
        config = NotificationConfig(
            channel=NotificationChannel.DISCORD,
            webhook_url="https://discord.com/webhook/123",
            enabled=True,
            events=[NotificationType.WORKFLOW_FAILED],
            repository_filter=["org/repo1"],
        )
        assert config.channel == NotificationChannel.DISCORD
        assert config.webhook_url == "https://discord.com/webhook/123"
        assert NotificationType.WORKFLOW_FAILED in config.events


class TestWorkflowFailedPayload:
    """Tests for WorkflowFailedPayload."""

    @pytest.mark.unit
    def test_creation(self) -> None:
        payload = WorkflowFailedPayload(
            repository_name="org/repo",
            workflow_name="CI",
            run_number=42,
            branch="main",
            commit_sha="abc123",
            actor="user1",
        )
        assert payload.repository_name == "org/repo"
        assert payload.run_number == 42
        assert payload.failure_reason == ""
        assert payload.run_url == ""


class TestDailySummaryPayload:
    """Tests for DailySummaryPayload."""

    @pytest.mark.unit
    def test_creation(self) -> None:
        payload = DailySummaryPayload(
            date="2024-06-15",
            total_runs=100,
            successful_runs=90,
            failed_runs=10,
            success_rate=90.0,
            repositories_monitored=5,
        )
        assert payload.total_runs == 100
        assert payload.success_rate == 90.0
        assert payload.top_failures == []

    @pytest.mark.unit
    def test_with_failures(self) -> None:
        payload = DailySummaryPayload(
            date="2024-06-15",
            total_runs=50,
            successful_runs=40,
            failed_runs=10,
            success_rate=80.0,
            top_failures=[{"name": "CI", "count": 5}],
        )
        assert len(payload.top_failures) == 1
        assert payload.top_failures[0]["name"] == "CI"
