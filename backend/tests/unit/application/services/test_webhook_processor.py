"""Tests for webhook processor service."""
import hashlib
import hmac
from unittest.mock import AsyncMock

import pytest

from app.application.services.webhook_processor import (
    GitHubWebhookValidator,
    ProcessResult,
    WebhookProcessor,
)
from app.core.exceptions import WebhookValidationError


class TestGitHubWebhookValidator:
    """Test suite for GitHub webhook signature validation."""

    @pytest.fixture
    def secret(self) -> str:
        """Webhook secret."""
        return "test-webhook-secret"

    @pytest.fixture
    def validator(self, secret: str) -> GitHubWebhookValidator:
        """Create validator instance."""
        return GitHubWebhookValidator(secret)

    def _generate_signature(self, payload: bytes, secret: str) -> str:
        """Generate valid signature for testing."""
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    def test_validate_valid_signature(self, validator: GitHubWebhookValidator, secret: str) -> None:
        """Should accept valid signature."""
        payload = b'{"action": "completed"}'
        signature = self._generate_signature(payload, secret)

        assert validator.validate(payload, signature) is True

    def test_validate_invalid_signature(self, validator: GitHubWebhookValidator) -> None:
        """Should reject invalid signature."""
        payload = b'{"action": "completed"}'
        signature = "sha256=invalid_signature_here"

        assert validator.validate(payload, signature) is False

    def test_validate_missing_prefix(self, validator: GitHubWebhookValidator) -> None:
        """Should reject signature without sha256 prefix."""
        payload = b'{"action": "completed"}'
        # Valid hash but missing prefix
        signature = hmac.new(
            b"test-webhook-secret",
            payload,
            hashlib.sha256,
        ).hexdigest()

        assert validator.validate(payload, signature) is False

    def test_validate_empty_payload(self, validator: GitHubWebhookValidator, secret: str) -> None:
        """Should validate empty payload correctly."""
        payload = b""
        signature = self._generate_signature(payload, secret)

        assert validator.validate(payload, signature) is True

    def test_validate_tampered_payload(
        self, validator: GitHubWebhookValidator, secret: str
    ) -> None:
        """Should reject if payload was tampered."""
        original_payload = b'{"action": "completed"}'
        signature = self._generate_signature(original_payload, secret)

        tampered_payload = b'{"action": "failed"}'
        assert validator.validate(tampered_payload, signature) is False


class TestWebhookProcessor:
    """Test suite for webhook processing."""

    @pytest.fixture
    def validator(self) -> GitHubWebhookValidator:
        """Create validator."""
        return GitHubWebhookValidator("test-secret")

    @pytest.fixture
    def idempotency_store(self) -> AsyncMock:
        """Create mock idempotency store."""
        store = AsyncMock()
        store.exists.return_value = False
        return store

    @pytest.fixture
    def processor(
        self, validator: GitHubWebhookValidator, idempotency_store: AsyncMock
    ) -> WebhookProcessor:
        """Create processor instance."""
        return WebhookProcessor(validator, idempotency_store)

    def _generate_signature(self, payload: bytes, secret: str = "test-secret") -> str:
        """Generate valid signature for testing."""
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"

    @pytest.mark.asyncio
    async def test_process_valid_webhook(
        self, processor: WebhookProcessor, idempotency_store: AsyncMock
    ) -> None:
        """Should process valid webhook successfully."""
        payload = b'{"action": "completed"}'
        signature = self._generate_signature(payload)
        delivery_id = "test-delivery-123"

        result = await processor.process(
            payload=payload,
            signature=signature,
            event_type="workflow_run",
            delivery_id=delivery_id,
        )

        assert result.status == "queued"
        assert result.delivery_id == delivery_id
        idempotency_store.mark_processed.assert_called_once_with(delivery_id)

    @pytest.mark.asyncio
    async def test_process_duplicate_webhook(
        self, processor: WebhookProcessor, idempotency_store: AsyncMock
    ) -> None:
        """Should detect duplicate webhook."""
        payload = b'{"action": "completed"}'
        signature = self._generate_signature(payload)
        delivery_id = "duplicate-delivery"

        # Mark as already processed
        idempotency_store.exists.return_value = True

        result = await processor.process(
            payload=payload,
            signature=signature,
            event_type="workflow_run",
            delivery_id=delivery_id,
        )

        assert result.status == "duplicate"
        assert result.delivery_id == delivery_id
        idempotency_store.mark_processed.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_invalid_signature_raises(
        self, processor: WebhookProcessor
    ) -> None:
        """Should raise error for invalid signature."""
        payload = b'{"action": "completed"}'
        invalid_signature = "sha256=invalid"

        with pytest.raises(WebhookValidationError):
            await processor.process(
                payload=payload,
                signature=invalid_signature,
                event_type="workflow_run",
                delivery_id="test-delivery",
            )


class TestProcessResult:
    """Test suite for ProcessResult dataclass."""

    def test_create_queued_result(self) -> None:
        """Should create queued result."""
        result = ProcessResult(
            status="queued",
            delivery_id="test-123",
        )

        assert result.status == "queued"
        assert result.delivery_id == "test-123"
        assert result.message is None

    def test_create_result_with_message(self) -> None:
        """Should create result with message."""
        result = ProcessResult(
            status="duplicate",
            delivery_id="test-456",
            message="Already processed",
        )

        assert result.status == "duplicate"
        assert result.message == "Already processed"
