"""Unit tests for notification_service."""

from unittest.mock import AsyncMock

import pytest

from app.application.services.notification_service import (
    NotificationResult,
    NotificationService,
    SlackSender,
)
from app.domain.entities.notification import (
    Notification,
    NotificationChannel,
    NotificationConfig,
    NotificationType,
)


def _slack_config(enabled: bool = True) -> NotificationConfig:
    return NotificationConfig(
        channel=NotificationChannel.SLACK,
        webhook_url="https://hooks.slack.com/test",
        enabled=enabled,
    )


def _discord_config(enabled: bool = True) -> NotificationConfig:
    return NotificationConfig(
        channel=NotificationChannel.DISCORD,
        webhook_url="https://discord.com/api/webhooks/test",
        enabled=enabled,
    )


@pytest.mark.unit
class TestNotificationService:
    """Tests for NotificationService."""

    async def test_notify_sends_to_configured_channels(self) -> None:
        service = NotificationService(configs=[_slack_config()])

        # Mock the sender
        mock_sender = AsyncMock()
        mock_sender.send = AsyncMock(
            return_value=NotificationResult(success=True, message="ok")
        )
        service._senders[NotificationChannel.SLACK] = mock_sender

        results = await service.notify(
            notification_type=NotificationType.WORKFLOW_FAILED,
            title="Build failed",
            message="Something broke",
        )

        assert NotificationChannel.SLACK in results
        assert results[NotificationChannel.SLACK].success is True
        mock_sender.send.assert_called_once()

    async def test_notify_skips_disabled_channels(self) -> None:
        service = NotificationService(configs=[_slack_config(enabled=False)])

        results = await service.notify(
            notification_type=NotificationType.WORKFLOW_FAILED,
            title="Test",
            message="msg",
        )

        assert len(results) == 0

    async def test_notify_with_no_configs(self) -> None:
        service = NotificationService(configs=[])

        results = await service.notify(
            notification_type=NotificationType.WORKFLOW_FAILED,
            title="Test",
            message="msg",
        )

        assert len(results) == 0

    async def test_create_sender_creates_slack(self) -> None:
        service = NotificationService(configs=[_slack_config()])
        assert NotificationChannel.SLACK in service._senders
        assert isinstance(service._senders[NotificationChannel.SLACK], SlackSender)

    async def test_notify_filters_by_event_type(self) -> None:
        config = NotificationConfig(
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            enabled=True,
            events=[NotificationType.DAILY_SUMMARY],  # Only daily summary
        )
        service = NotificationService(configs=[config])

        mock_sender = AsyncMock()
        mock_sender.send = AsyncMock(
            return_value=NotificationResult(success=True, message="ok")
        )
        service._senders[NotificationChannel.SLACK] = mock_sender

        # This type is not in the events list
        results = await service.notify(
            notification_type=NotificationType.WORKFLOW_FAILED,
            title="Test",
            message="msg",
        )

        assert len(results) == 0
        mock_sender.send.assert_not_called()


@pytest.mark.unit
class TestSlackSender:
    """Tests for SlackSender message formatting."""

    def test_format_message_includes_title_and_body(self) -> None:
        sender = SlackSender("https://hooks.slack.com/test")
        notification = Notification.create(
            notification_type=NotificationType.WORKFLOW_FAILED,
            channel=NotificationChannel.SLACK,
            title="Build Failed",
            message="Check the logs",
        )

        payload = sender.format_message(notification)

        assert "attachments" in payload
        blocks = payload["attachments"][0]["blocks"]
        assert any("Build Failed" in str(b) for b in blocks)
        assert any("Check the logs" in str(b) for b in blocks)
