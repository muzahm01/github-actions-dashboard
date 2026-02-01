"""Analysis-related domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.events.base import DomainEvent


@dataclass
class ErrorAnalysisRequested(DomainEvent):
    """Event emitted when error analysis is requested."""

    log_id: int = 0
    job_id: int = 0
    run_id: int = 0
    priority: str = "normal"  # "high", "normal", "low"
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "error_analysis.requested"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "log_id": self.log_id,
            "job_id": self.job_id,
            "run_id": self.run_id,
            "priority": self.priority,
        }


@dataclass
class ErrorAnalysisCompleted(DomainEvent):
    """Event emitted when error analysis completes."""

    analysis_id: int = 0
    log_id: int = 0
    job_id: int = 0
    run_id: int = 0
    root_cause: str = ""
    error_summary: str = ""
    confidence_score: float = 0.0
    tokens_used: int = 0
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "error_analysis.completed"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "analysis_id": self.analysis_id,
            "log_id": self.log_id,
            "job_id": self.job_id,
            "run_id": self.run_id,
            "root_cause": self.root_cause,
            "error_summary": self.error_summary,
            "confidence_score": self.confidence_score,
            "tokens_used": self.tokens_used,
        }


@dataclass
class ErrorAnalysisFailed(DomainEvent):
    """Event emitted when error analysis fails."""

    log_id: int = 0
    job_id: int = 0
    error_message: str = ""
    retry_count: int = 0
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "error_analysis.failed"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "log_id": self.log_id,
            "job_id": self.job_id,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }
