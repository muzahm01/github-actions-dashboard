"""Tests for security utilities: API key auth, middlewares, URL validation."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.api.v1.security import (
    RateLimitMiddleware,
    _rate_limit_buckets,
    escape_like_pattern,
    validate_webhook_url,
    verify_api_key,
)
from app.config import Settings

pytestmark = pytest.mark.unit


class TestVerifyApiKey:
    """Tests for verify_api_key dependency."""

    @pytest.fixture
    def prod_settings(self) -> MagicMock:
        settings = MagicMock(spec=Settings)
        settings.environment = "production"
        settings.secret_key = "correct-key"
        settings.enable_dev_auth_bypass = False
        return settings

    @pytest.fixture
    def dev_settings(self) -> MagicMock:
        settings = MagicMock(spec=Settings)
        settings.environment = "development"
        settings.secret_key = "correct-key"
        settings.enable_dev_auth_bypass = True
        return settings

    @pytest.mark.asyncio
    async def test_valid_api_key_returns_key(self, prod_settings: MagicMock) -> None:
        result = await verify_api_key(api_key="correct-key", settings=prod_settings)
        assert result == "correct-key"

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_401(self, prod_settings: MagicMock) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(api_key=None, settings=prod_settings)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_api_key_raises_403(self, prod_settings: MagicMock) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(api_key="wrong-key", settings=prod_settings)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_dev_bypass_skips_auth(self, dev_settings: MagicMock) -> None:
        result = await verify_api_key(api_key=None, settings=dev_settings)
        assert result == "dev-bypass"

    @pytest.mark.asyncio
    async def test_dev_bypass_disabled_requires_key(self) -> None:
        from fastapi import HTTPException

        settings = MagicMock(spec=Settings)
        settings.environment = "development"
        settings.enable_dev_auth_bypass = False
        settings.secret_key = "key"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(api_key=None, settings=settings)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_testing_bypass_works(self) -> None:
        settings = MagicMock(spec=Settings)
        settings.environment = "testing"
        settings.enable_dev_auth_bypass = True
        settings.secret_key = "key"

        result = await verify_api_key(api_key=None, settings=settings)
        assert result == "dev-bypass"


class TestValidateWebhookUrl:
    """Tests for SSRF-safe URL validation."""

    def test_valid_https_url(self) -> None:
        url = "https://hooks.slack.com/services/test"
        assert validate_webhook_url(url) == url

    def test_valid_http_url(self) -> None:
        url = "http://hooks.slack.com/services/test"
        assert validate_webhook_url(url) == url

    def test_rejects_unsupported_scheme(self) -> None:
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            validate_webhook_url("ftp://example.com")

    def test_rejects_no_hostname(self) -> None:
        with pytest.raises(ValueError, match="valid hostname"):
            validate_webhook_url("https://")

    def test_rejects_localhost(self) -> None:
        with pytest.raises(ValueError, match="internal host"):
            validate_webhook_url("https://localhost/webhook")

    def test_rejects_metadata_host(self) -> None:
        with pytest.raises(ValueError, match="internal"):
            validate_webhook_url("https://metadata.google.internal/something")

    def test_rejects_metadata_shortname(self) -> None:
        with pytest.raises(ValueError, match="internal host"):
            validate_webhook_url("https://metadata/computeMetadata")

    def test_rejects_private_ipv4_10(self) -> None:
        with pytest.raises(ValueError, match="internal/private"):
            validate_webhook_url("https://10.0.0.1/webhook")

    def test_rejects_private_ipv4_172(self) -> None:
        with pytest.raises(ValueError, match="internal/private"):
            validate_webhook_url("https://172.16.0.1/webhook")

    def test_rejects_private_ipv4_192(self) -> None:
        with pytest.raises(ValueError, match="internal/private"):
            validate_webhook_url("https://192.168.1.1/webhook")

    def test_rejects_loopback_127(self) -> None:
        with pytest.raises(ValueError, match="internal/private"):
            validate_webhook_url("https://127.0.0.1/webhook")

    def test_rejects_link_local(self) -> None:
        with pytest.raises(ValueError, match="internal/private"):
            validate_webhook_url("https://169.254.169.254/latest/meta-data/")

    def test_rejects_ipv6_loopback(self) -> None:
        with pytest.raises(ValueError, match="internal/private"):
            validate_webhook_url("https://[::1]/webhook")

    def test_rejects_redis_host(self) -> None:
        with pytest.raises(ValueError, match="internal host"):
            validate_webhook_url("https://redis:6379/webhook")

    def test_rejects_postgres_host(self) -> None:
        with pytest.raises(ValueError, match="internal host"):
            validate_webhook_url("https://postgres:5432/webhook")

    def test_allows_external_ip(self) -> None:
        url = "https://203.0.113.1/webhook"
        assert validate_webhook_url(url) == url


class TestEscapeLikePattern:
    """Tests for SQL LIKE pattern escaping."""

    def test_escapes_percent(self) -> None:
        assert escape_like_pattern("100%") == "100\\%"

    def test_escapes_underscore(self) -> None:
        assert escape_like_pattern("foo_bar") == "foo\\_bar"

    def test_escapes_backslash(self) -> None:
        assert escape_like_pattern("a\\b") == "a\\\\b"

    def test_escapes_all_special_chars(self) -> None:
        assert escape_like_pattern("%_\\") == "\\%\\_\\\\"

    def test_leaves_normal_text_unchanged(self) -> None:
        assert escape_like_pattern("hello world") == "hello world"

    def test_empty_string(self) -> None:
        assert escape_like_pattern("") == ""


class TestMemoryRateLimit:
    """Tests for the in-memory token bucket fallback."""

    def setup_method(self) -> None:
        _rate_limit_buckets.clear()

    def test_first_request_allowed(self) -> None:
        result = RateLimitMiddleware._check_memory_rate_limit("1.2.3.4", 10.0, 60.0)
        assert result is False

    def test_exceeding_limit_is_blocked(self) -> None:
        ip = "1.2.3.5"
        for _ in range(10):
            RateLimitMiddleware._check_memory_rate_limit(ip, 10.0, 60.0)
        result = RateLimitMiddleware._check_memory_rate_limit(ip, 10.0, 60.0)
        assert result is True

    def test_different_ips_independent(self) -> None:
        for _ in range(10):
            RateLimitMiddleware._check_memory_rate_limit("ip-a", 10.0, 60.0)
        result = RateLimitMiddleware._check_memory_rate_limit("ip-b", 10.0, 60.0)
        assert result is False
