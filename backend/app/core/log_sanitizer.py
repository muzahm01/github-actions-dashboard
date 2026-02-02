"""Log sanitization to redact sensitive data."""

import logging
import re
from typing import Any

# Patterns for sensitive data
SENSITIVE_PATTERNS = [
    # API keys and tokens
    (re.compile(r"(ghp_[a-zA-Z0-9]{36})"), "[GITHUB_TOKEN_REDACTED]"),
    (re.compile(r"(gho_[a-zA-Z0-9]{36})"), "[GITHUB_OAUTH_REDACTED]"),
    (re.compile(r"(ghu_[a-zA-Z0-9]{36})"), "[GITHUB_USER_TOKEN_REDACTED]"),
    (re.compile(r"(ghs_[a-zA-Z0-9]{36})"), "[GITHUB_SERVER_TOKEN_REDACTED]"),
    (re.compile(r"(ghr_[a-zA-Z0-9]{36})"), "[GITHUB_REFRESH_TOKEN_REDACTED]"),
    (re.compile(r"(sk-ant-[a-zA-Z0-9-_]{40,})"), "[ANTHROPIC_KEY_REDACTED]"),
    (re.compile(r"(sk-[a-zA-Z0-9]{48})"), "[OPENAI_KEY_REDACTED]"),
    (re.compile(r"(gha_[a-zA-Z0-9_-]{43})"), "[API_KEY_REDACTED]"),
    # Bearer tokens
    (re.compile(r"(Bearer\s+[a-zA-Z0-9._-]+)"), "Bearer [TOKEN_REDACTED]"),
    # Basic auth
    (re.compile(r"(Basic\s+[a-zA-Z0-9+/=]+)"), "Basic [CREDENTIALS_REDACTED]"),
    # Passwords in URLs
    (re.compile(r"(://[^:]+:)[^@]+(@)"), r"\1[PASSWORD_REDACTED]\2"),
    # Generic password patterns
    (re.compile(r'(["\']?password["\']?\s*[:=]\s*)["\']?[^"\'\s,}]+["\']?', re.I), r"\1[REDACTED]"),
    (re.compile(r'(["\']?secret["\']?\s*[:=]\s*)["\']?[^"\'\s,}]+["\']?', re.I), r"\1[REDACTED]"),
    (re.compile(r'(["\']?token["\']?\s*[:=]\s*)["\']?[^"\'\s,}]+["\']?', re.I), r"\1[REDACTED]"),
    (re.compile(r'(["\']?api[_-]?key["\']?\s*[:=]\s*)["\']?[^"\'\s,}]+["\']?', re.I), r"\1[REDACTED]"),
    # AWS keys
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "[AWS_KEY_REDACTED]"),
    # Private keys
    (re.compile(r"(-----BEGIN [A-Z ]+ PRIVATE KEY-----)"), "[PRIVATE_KEY_REDACTED]"),
    # JWT tokens (complete redaction)
    (re.compile(r"(eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)"), "[JWT_REDACTED]"),
]

# Fields that should be completely redacted in structured logs
SENSITIVE_FIELDS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "authorization",
    "auth",
    "credentials",
    "private_key",
    "privatekey",
    "access_token",
    "refresh_token",
    "session_id",
    "sessionid",
    "cookie",
    "x-api-key",
    "x-auth-token",
}


def sanitize_string(value: str) -> str:
    """Sanitize a string by redacting sensitive patterns."""
    result = value
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_dict(data: dict[str, Any], depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
    """Recursively sanitize a dictionary."""
    if depth > max_depth:
        return {"_truncated": "Max depth exceeded"}

    result = {}
    for key, value in data.items():
        # Check if key is sensitive
        key_lower = key.lower().replace("-", "_")
        if key_lower in SENSITIVE_FIELDS:
            result[key] = "[REDACTED]"
        elif isinstance(value, str):
            result[key] = sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, depth + 1, max_depth)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, depth + 1, max_depth) if isinstance(item, dict)
                else sanitize_string(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value

    return result


class SanitizingLogFilter(logging.Filter):
    """
    Logging filter that sanitizes sensitive data from log records.

    Applies to both the message and any extra fields.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize the log record."""
        # Sanitize the message
        if record.msg and isinstance(record.msg, str):
            record.msg = sanitize_string(record.msg)

        # Sanitize args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_dict(record.args)  # type: ignore[assignment]
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    sanitize_string(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        # Sanitize extra fields (stored in __dict__)
        for key in list(record.__dict__.keys()):
            if key.startswith("_") or key in logging.LogRecord.__dict__:
                continue
            value = record.__dict__[key]
            key_lower = key.lower().replace("-", "_")
            if key_lower in SENSITIVE_FIELDS:
                record.__dict__[key] = "[REDACTED]"
            elif isinstance(value, str):
                record.__dict__[key] = sanitize_string(value)
            elif isinstance(value, dict):
                record.__dict__[key] = sanitize_dict(value)  # type: ignore[assignment]

        return True


class SanitizingJsonFormatter(logging.Formatter):
    """
    JSON log formatter that sanitizes sensitive data.

    Extends pythonjsonlogger to add sanitization.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from pythonjsonlogger import jsonlogger

        self._json_formatter = jsonlogger.JsonFormatter(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format the record as sanitized JSON."""
        # Let the JSON formatter do its work
        json_output = self._json_formatter.format(record)

        # Sanitize the final output
        return sanitize_string(json_output)


def setup_sanitized_logging(level: str = "INFO") -> None:
    """Configure logging with sanitization enabled."""
    import sys

    from pythonjsonlogger import jsonlogger

    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create handler with sanitizing filter
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SanitizingLogFilter())

    # Use JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
