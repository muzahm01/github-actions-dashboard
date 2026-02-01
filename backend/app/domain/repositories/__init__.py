"""Domain repository interfaces module."""

from app.domain.repositories.interfaces import (
    RepositoryRepository,
    WorkflowRepository,
    WorkflowRunRepository,
    JobRepository,
    LogRepository,
    ErrorAnalysisRepository,
    TestResultRepository,
    NotificationRepository,
    TrendRepository,
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
