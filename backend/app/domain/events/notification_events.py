"""Notification-related domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.events.base import DomainEvent


@dataclass
class NotificationRequested(DomainEvent):
    """Event emitted when a notification is requested."""

    notification_type: str = ""
    channel: str = ""
    title: str = ""
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "notification.requested"

    def _payload_dict(self) -> dict[str, Any]:
        """Return event payload."""
        return {
            "notification_type": self.notification_type,
            "channel": self.channel,
            "title": self.title,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass
class NotificationSent(DomainEvent):
    """Event emitted when a notification is successfully sent."""

    notification_id: int = 0
    channel: str = ""
    notification_type: str = ""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "notification.sent"

    def _payload_dict(self) -> dict[str, Any]:
        """Return event payload."""
        return {
            "notification_id": self.notification_id,
            "channel": self.channel,
            "notification_type": self.notification_type,
        }


@dataclass
class NotificationFailed(DomainEvent):
    """Event emitted when a notification fails to send."""

    notification_id: int = 0
    channel: str = ""
    error_message: str = ""
    retry_count: int = 0
    will_retry: bool = False
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "notification.failed"

    def _payload_dict(self) -> dict[str, Any]:
        """Return event payload."""
        return {
            "notification_id": self.notification_id,
            "channel": self.channel,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "will_retry": self.will_retry,
        }
