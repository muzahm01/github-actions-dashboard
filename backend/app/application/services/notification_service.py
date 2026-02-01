"""Notification service for sending alerts via Slack, Discord, etc."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.domain.entities.notification import (
    Notification,
    NotificationChannel,
    NotificationType,
    NotificationConfig,
    WorkflowFailedPayload,
    DailySummaryPayload,
)

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of notification send attempt."""

    success: bool
    message: str = ""
    error: str | None = None


class NotificationSender(ABC):
    """Abstract base for notification senders."""

    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult:
        """Send notification."""
        ...

    @abstractmethod
    def format_message(self, notification: Notification) -> dict:
        """Format notification for the channel."""
        ...


class SlackSender(NotificationSender):
    """Slack notification sender using webhooks."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize Slack sender."""
        self._webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, notification: Notification) -> NotificationResult:
        """Send notification to Slack."""
        try:
            payload = self.format_message(notification)
            response = await self._client.post(
                self._webhook_url,
                json=payload,
            )
            response.raise_for_status()

            return NotificationResult(success=True, message="Sent to Slack")

        except httpx.HTTPStatusError as e:
            logger.error(f"Slack API error: {e}")
            return NotificationResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return NotificationResult(success=False, error=str(e))

    def format_message(self, notification: Notification) -> dict:
        """Format notification as Slack message."""
        # Get color based on notification type
        color = self._get_color(notification.notification_type)

        # Build blocks for rich formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": notification.title,
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": notification.message,
                },
            },
        ]

        # Add context fields from metadata
        if notification.metadata:
            fields = []
            for key, value in notification.metadata.items():
                if key not in ("run_url",):
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key.replace('_', ' ').title()}:* {value}",
                    })

            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10],  # Max 10 fields
                })

            # Add action button for run URL
            if notification.metadata.get("run_url"):
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Run",
                                "emoji": True,
                            },
                            "url": notification.metadata["run_url"],
                        }
                    ],
                })

        return {
            "attachments": [{"color": color, "blocks": blocks}],
        }

    def _get_color(self, notification_type: NotificationType) -> str:
        """Get color for notification type."""
        colors = {
            NotificationType.WORKFLOW_FAILED: "#dc3545",  # Red
            NotificationType.WORKFLOW_SUCCEEDED: "#28a745",  # Green
            NotificationType.ERROR_ANALYSIS_COMPLETE: "#17a2b8",  # Info blue
            NotificationType.DAILY_SUMMARY: "#6c757d",  # Gray
            NotificationType.TREND_ALERT: "#ffc107",  # Warning yellow
        }
        return colors.get(notification_type, "#6c757d")


class DiscordSender(NotificationSender):
    """Discord notification sender using webhooks."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize Discord sender."""
        self._webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, notification: Notification) -> NotificationResult:
        """Send notification to Discord."""
        try:
            payload = self.format_message(notification)
            response = await self._client.post(
                self._webhook_url,
                json=payload,
            )
            response.raise_for_status()

            return NotificationResult(success=True, message="Sent to Discord")

        except httpx.HTTPStatusError as e:
            logger.error(f"Discord API error: {e}")
            return NotificationResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return NotificationResult(success=False, error=str(e))

    def format_message(self, notification: Notification) -> dict:
        """Format notification as Discord embed."""
        color = self._get_color(notification.notification_type)

        embed = {
            "title": notification.title,
            "description": notification.message,
            "color": color,
            "fields": [],
        }

        # Add metadata as fields
        if notification.metadata:
            for key, value in notification.metadata.items():
                if key not in ("run_url",) and value:
                    embed["fields"].append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": True,
                    })

            # Add URL if available
            if notification.metadata.get("run_url"):
                embed["url"] = notification.metadata["run_url"]

        return {
            "embeds": [embed],
        }

    def _get_color(self, notification_type: NotificationType) -> int:
        """Get color for notification type (Discord uses decimal colors)."""
        colors = {
            NotificationType.WORKFLOW_FAILED: 14370117,  # Red
            NotificationType.WORKFLOW_SUCCEEDED: 2664261,  # Green
            NotificationType.ERROR_ANALYSIS_COMPLETE: 1554744,  # Info blue
            NotificationType.DAILY_SUMMARY: 7105644,  # Gray
            NotificationType.TREND_ALERT: 16760576,  # Warning yellow
        }
        return colors.get(notification_type, 7105644)


class WebhookSender(NotificationSender):
    """Generic webhook sender for custom integrations."""

    def __init__(self, webhook_url: str) -> None:
        """Initialize webhook sender."""
        self._webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, notification: Notification) -> NotificationResult:
        """Send notification to generic webhook."""
        try:
            payload = self.format_message(notification)
            response = await self._client.post(
                self._webhook_url,
                json=payload,
            )
            response.raise_for_status()

            return NotificationResult(success=True, message="Sent to webhook")

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return NotificationResult(success=False, error=str(e))

    def format_message(self, notification: Notification) -> dict:
        """Format notification as generic JSON payload."""
        return {
            "type": notification.notification_type.value,
            "channel": notification.channel.value,
            "title": notification.title,
            "message": notification.message,
            "metadata": notification.metadata,
            "timestamp": notification.created_at.isoformat(),
        }


class NotificationStore(Protocol):
    """Protocol for notification persistence."""

    async def save(self, notification: Notification) -> Notification:
        """Save notification."""
        ...

    async def list_pending(self, limit: int = 100) -> list[Notification]:
        """List pending notifications."""
        ...


class NotificationService:
    """Service for managing and sending notifications."""

    def __init__(
        self,
        configs: list[NotificationConfig],
        store: NotificationStore | None = None,
    ) -> None:
        """Initialize notification service with configurations."""
        self._configs = {cfg.channel: cfg for cfg in configs}
        self._store = store
        self._senders: dict[NotificationChannel, NotificationSender] = {}

        # Initialize senders
        for config in configs:
            if config.enabled and config.webhook_url:
                self._senders[config.channel] = self._create_sender(config)

    def _create_sender(self, config: NotificationConfig) -> NotificationSender:
        """Create sender for channel."""
        if config.channel == NotificationChannel.SLACK:
            return SlackSender(config.webhook_url)
        elif config.channel == NotificationChannel.DISCORD:
            return DiscordSender(config.webhook_url)
        else:
            return WebhookSender(config.webhook_url)

    async def notify(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: dict | None = None,
        channels: list[NotificationChannel] | None = None,
    ) -> dict[NotificationChannel, NotificationResult]:
        """Send notification to configured channels."""
        results: dict[NotificationChannel, NotificationResult] = {}

        # Determine which channels to use
        target_channels = channels or list(self._senders.keys())

        for channel in target_channels:
            # Check if channel is configured
            config = self._configs.get(channel)
            if not config or not config.enabled:
                continue

            # Check if event type is enabled for this channel
            if config.events and notification_type not in config.events:
                continue

            # Create notification
            notification = Notification.create(
                notification_type=notification_type,
                channel=channel,
                title=title,
                message=message,
                metadata=metadata,
            )

            # Get sender and send
            sender = self._senders.get(channel)
            if sender:
                result = await sender.send(notification)
                results[channel] = result

                # Update notification status
                if result.success:
                    notification.mark_sent()
                else:
                    notification.mark_failed()

                # Persist if store available
                if self._store:
                    await self._store.save(notification)

        return results

    async def notify_workflow_failed(
        self,
        payload: WorkflowFailedPayload,
    ) -> dict[NotificationChannel, NotificationResult]:
        """Send workflow failed notification."""
        title = f"Workflow Failed: {payload.workflow_name}"
        message = (
            f"Repository: *{payload.repository_name}*\n"
            f"Branch: `{payload.branch}`\n"
            f"Commit: `{payload.commit_sha[:7]}`\n"
            f"Triggered by: {payload.actor}"
        )

        if payload.failure_reason:
            message += f"\n\nReason: {payload.failure_reason}"

        metadata = {
            "repository": payload.repository_name,
            "workflow": payload.workflow_name,
            "branch": payload.branch,
            "run_number": payload.run_number,
            "run_url": payload.run_url,
        }

        return await self.notify(
            notification_type=NotificationType.WORKFLOW_FAILED,
            title=title,
            message=message,
            metadata=metadata,
        )

    async def notify_daily_summary(
        self,
        payload: DailySummaryPayload,
    ) -> dict[NotificationChannel, NotificationResult]:
        """Send daily summary notification."""
        title = f"Daily Summary - {payload.date}"
        message = (
            f"*Total Runs:* {payload.total_runs}\n"
            f"*Successful:* {payload.successful_runs}\n"
            f"*Failed:* {payload.failed_runs}\n"
            f"*Success Rate:* {payload.success_rate:.1f}%"
        )

        if payload.top_failures:
            message += "\n\n*Top Failing Workflows:*\n"
            for failure in payload.top_failures[:5]:
                message += f"- {failure.get('name', 'Unknown')}: {failure.get('count', 0)} failures\n"

        metadata = {
            "date": payload.date,
            "total_runs": payload.total_runs,
            "success_rate": f"{payload.success_rate:.1f}%",
            "repositories": payload.repositories_monitored,
        }

        return await self.notify(
            notification_type=NotificationType.DAILY_SUMMARY,
            title=title,
            message=message,
            metadata=metadata,
        )

    async def process_pending(self) -> int:
        """Process pending notifications (for retry)."""
        if not self._store:
            return 0

        pending = await self._store.list_pending()
        processed = 0

        for notification in pending:
            if not notification.can_retry():
                continue

            sender = self._senders.get(notification.channel)
            if not sender:
                continue

            result = await sender.send(notification)

            if result.success:
                notification.mark_sent()
            else:
                notification.mark_failed()

            await self._store.save(notification)
            processed += 1

        return processed
