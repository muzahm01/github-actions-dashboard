"""Webhook processing service."""

from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import WebhookValidationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookEvent:
    """Validated webhook event."""

    event_type: str
    action: str
    delivery_id: str
    payload: dict


class WebhookValidator(Protocol):
    """Protocol for webhook signature validation."""

    def validate(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature."""
        ...


class IdempotencyStore(Protocol):
    """Protocol for idempotency tracking."""

    async def exists(self, delivery_id: str) -> bool:
        """Check if delivery has been processed."""
        ...

    async def mark_processed(self, delivery_id: str) -> None:
        """Mark delivery as processed."""
        ...


class GitHubWebhookValidator:
    """GitHub-specific webhook validation."""

    def __init__(self, secret: str) -> None:
        """Initialize with webhook secret.

        Raises ValueError if the secret is empty, because an empty HMAC key
        makes signature validation trivially bypassable.
        """
        if not secret:
            raise ValueError(
                "GITHUB_WEBHOOK_SECRET must not be empty. "
                "Configure a strong secret to enable webhook signature validation."
            )
        self._secret = secret.encode()

    def validate(self, payload: bytes, signature: str) -> bool:
        """Validate GitHub webhook signature."""
        if not signature or not signature.startswith("sha256="):
            return False

        expected = hmac.new(
            self._secret,
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)


@dataclass
class ProcessResult:
    """Result of webhook processing."""

    status: str  # "queued", "duplicate", "error"
    delivery_id: str
    message: str | None = None


class WebhookProcessor:
    """Process incoming webhooks with idempotency."""

    def __init__(
        self,
        validator: WebhookValidator,
        idempotency_store: IdempotencyStore,
    ) -> None:
        """Initialize webhook processor."""
        self._validator = validator
        self._idempotency = idempotency_store

    async def process(
        self,
        payload: bytes,
        signature: str,
        event_type: str,
        delivery_id: str,
    ) -> ProcessResult:
        """Process webhook with validation and idempotency."""
        # Validate signature
        if not self._validator.validate(payload, signature):
            logger.warning(
                "Invalid webhook signature",
                extra={"delivery_id": delivery_id},
            )
            raise WebhookValidationError()

        # Atomic idempotency check-and-set (prevents TOCTOU race)
        if hasattr(self._idempotency, "try_acquire"):
            acquired = await self._idempotency.try_acquire(delivery_id)
        else:
            # Fallback for stores that don't support atomic acquire
            if await self._idempotency.exists(delivery_id):
                acquired = False
            else:
                await self._idempotency.mark_processed(delivery_id)
                acquired = True

        if not acquired:
            logger.info(
                "Duplicate webhook received",
                extra={"delivery_id": delivery_id},
            )
            return ProcessResult(
                status="duplicate",
                delivery_id=delivery_id,
                message="Webhook already processed",
            )

        logger.info(
            "Webhook queued for processing",
            extra={
                "delivery_id": delivery_id,
                "event_type": event_type,
            },
        )

        return ProcessResult(
            status="queued",
            delivery_id=delivery_id,
        )


class RedisIdempotencyStore:
    """Redis-based idempotency store."""

    def __init__(self, redis_client, ttl_seconds: int = 86400) -> None:  # type: ignore[no-untyped-def]
        """Initialize with Redis client."""
        self._redis = redis_client
        self._ttl = ttl_seconds
        self._prefix = "webhook:delivery:"

    async def exists(self, delivery_id: str) -> bool:
        """Check if delivery has been processed."""
        key = f"{self._prefix}{delivery_id}"
        return await self._redis.exists(key) > 0

    async def mark_processed(self, delivery_id: str) -> None:
        """Mark delivery as processed with TTL (atomic SET NX)."""
        key = f"{self._prefix}{delivery_id}"
        await self._redis.set(key, "1", ex=self._ttl, nx=True)

    async def try_acquire(self, delivery_id: str) -> bool:
        """Atomically check-and-set — returns True if this is the first claim.

        Replaces the separate exists() + mark_processed() calls to avoid
        TOCTOU race conditions.
        """
        key = f"{self._prefix}{delivery_id}"
        # SET ... NX returns True only when the key did not already exist
        result = await self._redis.set(key, "1", ex=self._ttl, nx=True)
        return result is not None
