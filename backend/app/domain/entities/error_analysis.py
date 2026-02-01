"""ErrorAnalysis domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ErrorAnalysis:
    """Domain entity representing LLM error analysis."""

    id: int
    log_id: int
    root_cause: str
    error_summary: str
    suggested_fixes: list[str] = field(default_factory=list)
    prevention_tips: list[str] = field(default_factory=list)
    confidence_score: float = 0.5
    related_documentation: list[str] = field(default_factory=list)
    tokens_used: int = 0
    model_version: str = ""
    prompt_version: str = "v1"
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        log_id: int,
        root_cause: str,
        error_summary: str,
        suggested_fixes: list[str] | None = None,
        prevention_tips: list[str] | None = None,
        confidence_score: float = 0.5,
        related_documentation: list[str] | None = None,
        tokens_used: int = 0,
        model_version: str = "",
    ) -> ErrorAnalysis:
        """Create a new error analysis entity."""
        return cls(
            id=0,
            log_id=log_id,
            root_cause=root_cause,
            error_summary=error_summary,
            suggested_fixes=suggested_fixes or [],
            prevention_tips=prevention_tips or [],
            confidence_score=confidence_score,
            related_documentation=related_documentation or [],
            tokens_used=tokens_used,
            model_version=model_version,
            created_at=datetime.utcnow(),
        )

    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """Check if analysis has high confidence."""
        return self.confidence_score >= threshold

    def has_fixes(self) -> bool:
        """Check if analysis has suggested fixes."""
        return len(self.suggested_fixes) > 0

    @property
    def primary_fix(self) -> str | None:
        """Get the first suggested fix."""
        return self.suggested_fixes[0] if self.suggested_fixes else None
