"""Custom application exceptions."""

from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} with id {identifier} not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class GitHubAPIError(AppException):
    """GitHub API error."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(
            message=message,
            code="GITHUB_API_ERROR",
            status_code=status_code,
        )


class LLMError(AppException):
    """LLM API error."""

    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=502,
            details={"provider": provider},
        )


class WebhookValidationError(AppException):
    """Webhook validation failed."""

    def __init__(self, message: str = "Invalid webhook signature") -> None:
        super().__init__(
            message=message,
            code="WEBHOOK_VALIDATION_ERROR",
            status_code=401,
        )


class CacheError(AppException):
    """Cache operation error."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            status_code=500,
        )
