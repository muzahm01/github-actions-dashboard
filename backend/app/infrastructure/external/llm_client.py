"""LLM client for error analysis using Claude."""

import logging
import re
from dataclasses import asdict, dataclass

from anthropic import AsyncAnthropic

from app.config import Settings
from app.core.exceptions import LLMError
from app.infrastructure.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)


@dataclass
class ErrorAnalysisResult:
    """Result of LLM error analysis."""

    root_cause: str
    error_summary: str
    suggested_fixes: list[str]
    prevention_tips: list[str]
    confidence_score: float
    related_documentation: list[str]
    tokens_used: int


# System prompt containing the trusted instructions — separated from user data
_SYSTEM_PROMPT = (
    "You are an expert CI/CD debugger analyzing a GitHub Actions workflow failure. "
    "The user will provide an error log along with metadata (test framework name "
    "and job name). Analyze the log and respond with ONLY valid JSON in this format:\n"
    '{"root_cause": "detailed explanation", '
    '"error_summary": "brief 1-2 sentence summary", '
    '"suggested_fixes": ["fix 1", "fix 2"], '
    '"prevention_tips": ["tip 1", "tip 2"], '
    '"confidence_score": 0.85, '
    '"related_documentation": ["https://docs.example.com/..."]}\n\n'
    "Only respond with valid JSON, no additional text."
)

_SUMMARY_SYSTEM_PROMPT = (
    "You are a CI/CD expert. The user will provide test failure data. "
    "Summarize the failures in 2-3 sentences, identifying common patterns. "
    "Focus on the main issues."
)

# Maximum allowed length for metadata fields to prevent abuse
_MAX_METADATA_LENGTH = 200


def _sanitize_metadata(value: str) -> str:
    """Sanitize user-controlled metadata to mitigate prompt injection.

    Strips control characters, limits length, and removes patterns that could
    be used to manipulate LLM behaviour (e.g. fake system/instruction blocks).
    """
    # Limit length
    value = value[:_MAX_METADATA_LENGTH]
    # Remove control characters except newlines and tabs
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    # Strip patterns that look like prompt injection attempts
    value = re.sub(
        r"(system\s*:|<\s*/?system\s*>|INSTRUCTION|IGNORE\s+PREVIOUS|"
        r"forget\s+(all|everything|previous)|you\s+are\s+now)",
        "[FILTERED]",
        value,
        flags=re.IGNORECASE,
    )
    return value.strip()


class ClaudeClient:
    """Client for Claude API for error analysis."""

    def __init__(self, settings: Settings, cache: RedisCache | None = None) -> None:
        """Initialize with settings and optional cache."""
        self._api_key = settings.anthropic_api_key
        self._model = settings.claude_model
        self._max_tokens = settings.claude_max_tokens
        self._client: AsyncAnthropic | None = None
        self._cache = cache

    def _get_client(self) -> AsyncAnthropic:
        """Get or create Anthropic client."""
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def analyze_error(
        self,
        log_content: str,
        framework: str = "unknown",
        job_name: str = "unknown",
        use_cache: bool = True,
    ) -> ErrorAnalysisResult:
        """Analyze error log using Claude with optional caching."""
        import json

        # Check cache first if enabled
        if use_cache and self._cache:
            cached = await self._cache.get_analysis(log_content)
            if cached:
                logger.info("Returning cached error analysis")
                return ErrorAnalysisResult(
                    root_cause=cached.get("root_cause", ""),
                    error_summary=cached.get("error_summary", ""),
                    suggested_fixes=cached.get("suggested_fixes", []),
                    prevention_tips=cached.get("prevention_tips", []),
                    confidence_score=cached.get("confidence_score", 0.5),
                    related_documentation=cached.get("related_documentation", []),
                    tokens_used=cached.get("tokens_used", 0),
                )

        client = self._get_client()

        # Truncate log if too long (keep first and last portions)
        max_log_length = 15000
        truncated_log = log_content
        if len(log_content) > max_log_length:
            half = max_log_length // 2
            truncated_log = log_content[:half] + "\n\n... [truncated] ...\n\n" + log_content[-half:]

        # Sanitize user-controlled metadata to prevent prompt injection
        safe_framework = _sanitize_metadata(framework)
        safe_job_name = _sanitize_metadata(job_name)

        # Use structured message boundaries: system prompt for instructions,
        # user message for untrusted data wrapped in XML tags
        user_message = (
            "<error_log>\n"
            f"{truncated_log}\n"
            "</error_log>\n\n"
            f"<metadata>\n"
            f"Test Framework: {safe_framework}\n"
            f"Job Name: {safe_job_name}\n"
            f"</metadata>"
        )

        try:
            message = await client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            # Extract text content
            content = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise LLMError(
                        "Failed to parse LLM response as JSON", provider="claude"
                    ) from None

            analysis_result = ErrorAnalysisResult(
                root_cause=result.get("root_cause", "Unable to determine"),
                error_summary=result.get("error_summary", "Error analysis failed"),
                suggested_fixes=result.get("suggested_fixes", []),
                prevention_tips=result.get("prevention_tips", []),
                confidence_score=float(result.get("confidence_score", 0.5)),
                related_documentation=result.get("related_documentation", []),
                tokens_used=tokens_used,
            )

            # Cache the result using original log content for hash
            if self._cache:
                await self._cache.set_analysis(log_content, asdict(analysis_result))

            return analysis_result

        except LLMError:
            raise
        except Exception as e:
            logger.error(
                "Claude API error",
                extra={"error_type": type(e).__name__},
            )
            raise LLMError(f"Claude API error: {type(e).__name__}", provider="claude") from e

    async def summarize_failures(
        self, failures: list[dict[str, str]], max_failures: int = 10
    ) -> str:
        """Summarize multiple test failures."""
        client = self._get_client()

        # Sanitize failure data before including in prompt
        sanitized_parts: list[str] = []
        for f in failures[:max_failures]:
            test_name = _sanitize_metadata(f.get("test_name", "unknown"))
            error_msg = _sanitize_metadata(f.get("error_message", "unknown"))
            sanitized_parts.append(f"Test: {test_name}\nError: {error_msg}")

        failures_text = "\n\n".join(sanitized_parts)

        user_message = f"<test_failures>\n{failures_text}\n</test_failures>"

        try:
            message = await client.messages.create(
                model=self._model,
                max_tokens=500,
                system=_SUMMARY_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(
                "Claude API error",
                extra={"error_type": type(e).__name__},
            )
            raise LLMError(f"Claude API error: {type(e).__name__}", provider="claude") from e
