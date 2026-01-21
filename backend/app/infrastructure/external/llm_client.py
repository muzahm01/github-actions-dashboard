"""LLM client for error analysis using Claude."""

import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from app.config import Settings
from app.core.exceptions import LLMError

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


ERROR_ANALYSIS_PROMPT = """You are an expert CI/CD debugger analyzing a GitHub Actions workflow failure.

Analyze the following error log and provide:
1. Root cause analysis - what went wrong and why
2. A brief error summary (1-2 sentences)
3. Suggested fixes (actionable steps to resolve)
4. Prevention tips (how to avoid this in the future)
5. Confidence score (0.0 to 1.0) based on how certain you are
6. Related documentation links if applicable

Error Log:
```
{log_content}
```

Test Framework: {framework}
Job Name: {job_name}

Respond in this exact JSON format:
{{
    "root_cause": "detailed explanation of what caused the error",
    "error_summary": "brief 1-2 sentence summary",
    "suggested_fixes": ["fix 1", "fix 2", ...],
    "prevention_tips": ["tip 1", "tip 2", ...],
    "confidence_score": 0.85,
    "related_documentation": ["https://docs.example.com/..."]
}}

Only respond with valid JSON, no additional text."""


class ClaudeClient:
    """Client for Claude API for error analysis."""

    def __init__(self, settings: Settings) -> None:
        """Initialize with settings."""
        self._api_key = settings.anthropic_api_key
        self._model = settings.claude_model
        self._max_tokens = settings.claude_max_tokens
        self._client: AsyncAnthropic | None = None

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
    ) -> ErrorAnalysisResult:
        """Analyze error log using Claude."""
        import json

        client = self._get_client()

        # Truncate log if too long (keep first and last portions)
        max_log_length = 15000
        if len(log_content) > max_log_length:
            half = max_log_length // 2
            log_content = log_content[:half] + "\n\n... [truncated] ...\n\n" + log_content[-half:]

        prompt = ERROR_ANALYSIS_PROMPT.format(
            log_content=log_content,
            framework=framework,
            job_name=job_name,
        )

        try:
            message = await client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text content
            content = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re

                json_match = re.search(r"\{[\s\S]*\}", content)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise LLMError(
                        "Failed to parse LLM response as JSON", provider="claude"
                    ) from None

            return ErrorAnalysisResult(
                root_cause=result.get("root_cause", "Unable to determine"),
                error_summary=result.get("error_summary", "Error analysis failed"),
                suggested_fixes=result.get("suggested_fixes", []),
                prevention_tips=result.get("prevention_tips", []),
                confidence_score=float(result.get("confidence_score", 0.5)),
                related_documentation=result.get("related_documentation", []),
                tokens_used=tokens_used,
            )

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise LLMError(f"Claude API error: {e}", provider="claude") from e

    async def summarize_failures(self, failures: list[dict], max_failures: int = 10) -> str:
        """Summarize multiple test failures."""
        client = self._get_client()

        failures_text = "\n\n".join(
            f"Test: {f.get('test_name', 'unknown')}\nError: {f.get('error_message', 'unknown')}"
            for f in failures[:max_failures]
        )

        prompt = f"""Summarize these test failures in 2-3 sentences, identifying common patterns:

{failures_text}

Provide a concise summary focusing on the main issues."""

        try:
            message = await client.messages.create(
                model=self._model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise LLMError(f"Claude API error: {e}", provider="claude") from e
