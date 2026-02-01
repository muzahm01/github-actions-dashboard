"""Domain repository interfaces module."""

from app.domain.repositories.interfaces import (
    ErrorAnalysisRepository,
    JobRepository,
    LogRepository,
    NotificationRepository,
    RepositoryRepository,
    TestResultRepository,
    TrendRepository,
    WorkflowRepository,
    WorkflowRunRepository,
)

__all__ = [
    "RepositoryRepository",
    "WorkflowRepository",
    "WorkflowRunRepository",
    "JobRepository",
    "LogRepository",
    "ErrorAnalysisRepository",
    "TestResultRepository",
    "NotificationRepository",
    "TrendRepository",
]
