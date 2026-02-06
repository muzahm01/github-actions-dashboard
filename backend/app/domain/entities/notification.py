"""Notification domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal


class NotificationType(StrEnum):
    """Types of notifications."""

    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_SUCCEEDED = "workflow_succeeded"
    ERROR_ANALYSIS_COMPLETE = "error_analysis_complete"
    DAILY_SUMMARY = "daily_summary"
    TREND_ALERT = "trend_alert"


class NotificationChannel(StrEnum):
    """Notification delivery channels."""

    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"


NotificationStatus = Literal["pending", "sent", "failed", "retrying"]


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""

    channel: NotificationChannel
    webhook_url: str = ""
    enabled: bool = True
    events: list[NotificationType] = field(default_factory=list)
    repository_filter: list[str] = field(default_factory=list)  # Empty = all repos


@dataclass
class Notification:
    """Domain entity representing a notification."""

    id: int
    notification_type: NotificationType
    channel: NotificationChannel
    status: NotificationStatus
    title: str
    message: str
    metadata: dict = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    sent_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title: str,
        message: str,
        metadata: dict | None = None,
    ) -> Notification:
        """Create a new notification entity."""
        return cls(
            id=0,
            notification_type=notification_type,
            channel=channel,
            status="pending",
            title=title,
            message=message,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )

    def mark_sent(self) -> None:
        """Mark notification as sent."""
        self.status = "sent"
        self.sent_at = datetime.utcnow()

    def mark_failed(self) -> None:
        """Mark notification as failed."""
        if self.retry_count < self.max_retries:
            self.status = "retrying"
            self.retry_count += 1
        else:
            self.status = "failed"

    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return self.retry_count < self.max_retries

    def is_sent(self) -> bool:
        """Check if notification was sent."""
        return self.status == "sent"


@dataclass
class WorkflowFailedPayload:
    """Payload for workflow failed notification."""

    repository_name: str
    workflow_name: str
    run_number: int
    branch: str
    commit_sha: str
    actor: str
    failure_reason: str = ""
    run_url: str = ""


@dataclass
class DailySummaryPayload:
    """Payload for daily summary notification."""

    date: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    top_failures: list[dict] = field(default_factory=list)
    repositories_monitored: int = 0
