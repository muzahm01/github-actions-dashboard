"""Error analyzer service for analyzing workflow failures."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.domain.entities.error_analysis import ErrorAnalysis
from app.domain.entities.test_result import TestResult

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for error analysis."""

    log_id: int
    job_id: int
    log_content: str
    job_name: str = "unknown"
    framework: str = "unknown"
    test_result: TestResult | None = None
    custom_prompt: str | None = None
    priority: str = "normal"


@dataclass
class AnalysisResponse:
    """Response from error analysis."""

    analysis: ErrorAnalysis
    cached: bool = False
    tokens_used: int = 0


class LLMClient(Protocol):
    """Protocol for LLM client."""

    async def analyze_error(
        self,
        log_content: str,
        framework: str,
        job_name: str,
        use_cache: bool,
    ) -> LLMAnalysisResult:
        """Analyze error using LLM."""
        ...


@dataclass
class LLMAnalysisResult:
    """Result from LLM analysis."""

    root_cause: str
    error_summary: str
    suggested_fixes: list[str]
    prevention_tips: list[str]
    confidence_score: float
    related_documentation: list[str]
    tokens_used: int


class CacheClient(Protocol):
    """Protocol for cache operations."""

    async def get_analysis(self, log_content: str) -> dict | None:
        """Get cached analysis."""
        ...

    async def set_analysis(self, log_content: str, analysis: dict) -> None:
        """Cache analysis."""
        ...


class ErrorAnalyzerService:
    """Service for analyzing workflow errors using LLM."""

    def __init__(
        self,
        llm_client: LLMClient,
        cache_client: CacheClient | None = None,
    ) -> None:
        """Initialize error analyzer service."""
        self._llm = llm_client
        self._cache = cache_client

    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Analyze error and return analysis result."""
        logger.info(
            "Analyzing error",
            extra={
                "log_id": request.log_id,
                "job_id": request.job_id,
                "framework": request.framework,
            },
        )

        # Check cache first
        if self._cache:
            cached = await self._cache.get_analysis(request.log_content)
            if cached:
                logger.info("Returning cached analysis", extra={"log_id": request.log_id})
                analysis = ErrorAnalysis.create(
                    log_id=request.log_id,
                    root_cause=cached.get("root_cause", ""),
                    error_summary=cached.get("error_summary", ""),
                    suggested_fixes=cached.get("suggested_fixes", []),
                    prevention_tips=cached.get("prevention_tips", []),
                    confidence_score=cached.get("confidence_score", 0.5),
                    related_documentation=cached.get("related_documentation", []),
                    tokens_used=0,
                )
                return AnalysisResponse(analysis=analysis, cached=True)

        # Prepare log content for analysis
        log_content = self._prepare_log_content(request)

        # Call LLM for analysis
        result = await self._llm.analyze_error(
            log_content=log_content,
            framework=request.framework,
            job_name=request.job_name,
            use_cache=False,  # We handle caching here
        )

        # Create analysis entity
        analysis = ErrorAnalysis.create(
            log_id=request.log_id,
            root_cause=result.root_cause,
            error_summary=result.error_summary,
            suggested_fixes=result.suggested_fixes,
            prevention_tips=result.prevention_tips,
            confidence_score=result.confidence_score,
            related_documentation=result.related_documentation,
            tokens_used=result.tokens_used,
        )

        # Cache the result
        if self._cache:
            await self._cache.set_analysis(
                request.log_content,
                {
                    "root_cause": analysis.root_cause,
                    "error_summary": analysis.error_summary,
                    "suggested_fixes": analysis.suggested_fixes,
                    "prevention_tips": analysis.prevention_tips,
                    "confidence_score": analysis.confidence_score,
                    "related_documentation": analysis.related_documentation,
                },
            )

        logger.info(
            "Analysis completed",
            extra={
                "log_id": request.log_id,
                "confidence": analysis.confidence_score,
                "tokens": result.tokens_used,
            },
        )

        return AnalysisResponse(
            analysis=analysis,
            cached=False,
            tokens_used=result.tokens_used,
        )

    def _prepare_log_content(self, request: AnalysisRequest) -> str:
        """Prepare log content for analysis, including test result context."""
        content = request.log_content

        # Add test result context if available
        if request.test_result and request.test_result.has_failures():
            failure_summary = request.test_result.get_failure_summary()
            content = f"Test Failures:\n{failure_summary}\n\nFull Log:\n{content}"

        # Truncate if too long
        max_length = 15000
        if len(content) > max_length:
            half = max_length // 2
            content = content[:half] + "\n\n... [truncated] ...\n\n" + content[-half:]

        return content

    async def analyze_batch(
        self,
        requests: list[AnalysisRequest],
        max_concurrent: int = 5,
    ) -> list[AnalysisResponse]:
        """Analyze multiple errors in batch."""
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(req: AnalysisRequest) -> AnalysisResponse:
            async with semaphore:
                return await self.analyze(req)

        results = await asyncio.gather(
            *[analyze_with_semaphore(req) for req in requests],
            return_exceptions=True,
        )

        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Batch analysis failed for request {i}",
                    extra={"error": str(result)},
                )
            else:
                valid_results.append(result)

        return valid_results
