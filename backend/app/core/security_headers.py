"""Security headers middleware."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements OWASP recommended security headers.
    """

    # Content Security Policy
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "  # Vue may need inline scripts
        "style-src 'self' 'unsafe-inline'; "  # Allow inline styles for Vue
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "  # Allow WebSocket connections
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "object-src 'none'"
    )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy - don't leak URLs to third parties
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.CSP_POLICY

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Prevent caching of sensitive data
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # HSTS - enforce HTTPS (only in production)
        # Note: This should be set at the reverse proxy level in production
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class TrustedHostMiddleware:
    """
    Middleware to validate Host header.

    Prevents host header injection attacks.
    """

    def __init__(
        self,
        app: Callable,
        allowed_hosts: list[str] | None = None,
    ) -> None:
        self.app = app
        self.allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1"]

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Validate the host header."""
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        host = headers.get(b"host", b"").decode("latin-1").split(":")[0]

        # Allow any host if wildcard is configured
        if "*" in self.allowed_hosts:
            await self.app(scope, receive, send)
            return

        # Check if host is allowed
        if host not in self.allowed_hosts:
            if scope["type"] == "http":
                response = Response(
                    content="Invalid host header",
                    status_code=400,
                )
                await response(scope, receive, send)
                return
            # For WebSocket, just close the connection
            await send({"type": "websocket.close", "code": 1008})
            return

        await self.app(scope, receive, send)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size.

    Prevents memory exhaustion from large uploads.
    """

    def __init__(
        self,
        app: Callable,
        max_body_size: int = 10 * 1024 * 1024,  # 10 MB default
    ) -> None:
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Check content length before processing."""
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                if size > self.max_body_size:
                    return Response(
                        content="Request body too large",
                        status_code=413,
                        headers={
                            "Content-Type": "text/plain",
                            "Max-Size": str(self.max_body_size),
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)
