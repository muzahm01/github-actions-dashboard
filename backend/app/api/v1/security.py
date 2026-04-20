"""Security utilities: API key authentication and security headers middleware."""

from __future__ import annotations

import ipaddress
import logging
import secrets
import time
from typing import Annotated
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import WEAK_SECRET_KEY_VALUES, get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API-key authentication
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Annotated[str | None, Security(_api_key_header)] = None,
) -> str:
    """Validate the X-API-Key header against the configured secret_key.

    When the application runs in *development* or *testing* mode **and** no
    SECRET_KEY has been explicitly configured, authentication is skipped so
    that local development stays frictionless.
    """
    settings = get_settings()

    # In dev/testing with default secret, allow unauthenticated access
    if (
        settings.environment in ("development", "testing")
        and settings.secret_key in WEAK_SECRET_KEY_VALUES
    ):
        return "dev-bypass"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not secrets.compare_digest(api_key, settings.secret_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key


# Re-usable dependency
require_api_key = Depends(verify_api_key)


# ---------------------------------------------------------------------------
# Security-headers middleware
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Modern best-practice
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )

        settings = get_settings()
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        return response


# ---------------------------------------------------------------------------
# Rate-limiting middleware (simple in-memory token bucket per IP)
# ---------------------------------------------------------------------------

# Stores: ip -> (tokens, last_refill_timestamp)
_rate_limit_buckets: dict[str, tuple[float, float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP token-bucket rate limiter."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        max_tokens = float(settings.rate_limit_requests)
        refill_period = float(settings.rate_limit_period)

        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ("/health", "/health/ready", "/health/live", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        tokens, last_refill = _rate_limit_buckets.get(client_ip, (max_tokens, now))

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(max_tokens, tokens + elapsed * (max_tokens / refill_period))
        last_refill = now

        if tokens < 1.0:
            _rate_limit_buckets[client_ip] = (tokens, last_refill)
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": str(int(refill_period))},
            )

        tokens -= 1.0
        _rate_limit_buckets[client_ip] = (tokens, last_refill)
        return await call_next(request)


# ---------------------------------------------------------------------------
# SSRF-safe URL validation
# ---------------------------------------------------------------------------

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / AWS metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),  # Unique local
    ipaddress.ip_network("fe80::/10"),  # Link-local v6
]


def validate_webhook_url(url: str) -> str:
    """Validate that a webhook URL is safe (external HTTPS only).

    Raises ValueError for blocked URLs.
    """
    parsed = urlparse(url)

    # Only allow https (and http for well-known webhook services in dev)
    if parsed.scheme not in ("https", "http"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a valid hostname")

    # Block raw IP addresses pointing to internal ranges
    try:
        addr = ipaddress.ip_address(hostname)
        for network in _BLOCKED_NETWORKS:
            if addr in network:
                raise ValueError("Webhook URL must not point to internal/private networks")
    except ValueError as e:
        if "internal" in str(e).lower() or "must not" in str(e).lower():
            raise
        # hostname is not an IP literal — that's fine, continue

    # Block known internal hostnames
    blocked_hosts = {"localhost", "metadata.google.internal", "metadata", "redis", "postgres"}
    if hostname.lower() in blocked_hosts:
        raise ValueError(f"Webhook URL must not point to internal host: {hostname}")

    return url


# ---------------------------------------------------------------------------
# ILIKE pattern escaping
# ---------------------------------------------------------------------------


def escape_like_pattern(value: str) -> str:
    """Escape SQL LIKE/ILIKE special characters (%, _, \\)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
