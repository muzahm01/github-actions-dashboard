"""Rate limiting middleware using Redis."""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """
    Token bucket rate limiter using Redis.

    Implements a sliding window rate limiting algorithm.
    """

    def __init__(
        self,
        requests_per_period: int = 100,
        period_seconds: int = 60,
    ) -> None:
        self.requests_per_period = requests_per_period
        self.period_seconds = period_seconds
        self._redis_client: Redis | None = None

    async def _get_redis(self) -> Redis:
        """Get Redis client lazily."""
        if self._redis_client is None:
            import redis.asyncio as redis

            settings = get_settings()
            self._redis_client = redis.from_url(str(settings.redis_url))
        return self._redis_client

    def _get_client_identifier(self, request: Request) -> str:
        """Get a unique identifier for the client."""
        # Use API key if present, otherwise use IP
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # Hash the token to avoid storing sensitive data
            return f"token:{hashlib.sha256(token.encode()).hexdigest()[:16]}"

        # Use forwarded IP if behind proxy, otherwise use client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def is_rate_limited(self, request: Request) -> tuple[bool, int]:
        """
        Check if request should be rate limited.

        Returns (is_limited, retry_after_seconds).
        """
        try:
            redis = await self._get_redis()
            client_id = self._get_client_identifier(request)
            key = f"rate_limit:{client_id}"

            current_time = int(time.time())
            window_start = current_time - self.period_seconds

            # Use Redis pipeline for atomic operations
            async with redis.pipeline() as pipe:
                # Remove old entries outside the window
                await pipe.zremrangebyscore(key, 0, window_start)
                # Count requests in current window
                await pipe.zcard(key)
                # Add current request
                await pipe.zadd(key, {str(current_time): current_time})
                # Set expiry on the key
                await pipe.expire(key, self.period_seconds)
                results = await pipe.execute()

            request_count = results[1]

            if request_count >= self.requests_per_period:
                # Calculate retry-after
                oldest_request = await redis.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = int(oldest_request[0][1]) + self.period_seconds - current_time
                    return True, max(1, retry_after)
                return True, self.period_seconds

            return False, 0

        except Exception as e:
            # If Redis is unavailable, allow the request but log the error
            logger.warning(f"Rate limiting check failed: {e}")
            return False, 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Applies rate limiting to all requests except health checks.
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/health/ready", "/health/live", "/metrics"}

    def __init__(
        self,
        app: Callable,
        requests_per_period: int = 100,
        period_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_period, period_seconds)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Check rate limit
        is_limited, retry_after = await self.rate_limiter.is_rate_limited(request)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {self.rate_limiter._get_client_identifier(request)}"
            )
            raise RateLimitExceeded(retry_after)

        # Add rate limit headers to response
        response = await call_next(request)

        # Add informational headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_period)
        response.headers["X-RateLimit-Window"] = str(self.rate_limiter.period_seconds)

        return response


# Separate rate limiter for webhooks (more restrictive)
class WebhookRateLimiter(RateLimiter):
    """Rate limiter specifically for webhook endpoints."""

    def __init__(self) -> None:
        # 30 requests per minute for webhooks
        super().__init__(requests_per_period=30, period_seconds=60)

    def _get_client_identifier(self, request: Request) -> str:
        """Get identifier based on GitHub delivery ID or IP."""
        # Use X-GitHub-Delivery header if present
        delivery_id = request.headers.get("X-GitHub-Delivery")
        if delivery_id:
            return f"webhook:{delivery_id}"

        # Fall back to IP-based identification
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"webhook_ip:{client_ip}"


# Global webhook rate limiter instance
webhook_rate_limiter = WebhookRateLimiter()
