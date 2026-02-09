"""Base domain event classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID, uuid4


@dataclass
class DomainEvent(ABC):
    """Base class for domain events."""

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return event type identifier."""
        ...

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "payload": self._payload_dict(),
        }

    @abstractmethod
    def _payload_dict(self) -> dict[str, Any]:
        """Return event-specific payload as dictionary."""
        ...


class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        ...


class EventPublisher(Protocol):
    """Protocol for publishing domain events."""

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        ...

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events."""
        ...


class EventSubscriber(Protocol):
    """Protocol for subscribing to domain events."""

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe handler to event type."""
        ...

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe handler from event type."""
        ...


class InMemoryEventBus:
    """Simple in-memory event bus for domain events."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe handler to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe handler from event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all subscribed handlers."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            await handler.handle(event)

    async def publish_many(self, events: list[DomainEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)
