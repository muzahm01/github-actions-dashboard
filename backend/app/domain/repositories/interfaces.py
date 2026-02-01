"""Repository interface protocols."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.entities.repository import Repository
from app.domain.entities.workflow import Workflow
from app.domain.entities.workflow_run import WorkflowRun
from app.domain.entities.job import Job
from app.domain.entities.log import Log
from app.domain.entities.error_analysis import ErrorAnalysis
from app.domain.entities.test_result import TestResult
from app.domain.entities.notification import Notification
from app.domain.value_objects.pagination import Pagination, PaginatedResult
from app.domain.value_objects.time_range import TimeRange
from app.domain.value_objects.trend_data import TrendData, TrendPeriod, MetricType


@runtime_checkable
class RepositoryRepository(Protocol):
    """Repository interface for Repository entities."""

    async def get_by_id(self, repo_id: int) -> Repository | None:
        """Get repository by ID."""
        ...

    async def get_by_github_id(self, github_id: int) -> Repository | None:
        """Get repository by GitHub ID."""
        ...

    async def get_by_full_name(self, full_name: str) -> Repository | None:
        """Get repository by full name (owner/repo)."""
        ...

    async def list_active(self) -> list[Repository]:
        """List all active repositories."""
        ...

    async def list_all(self, pagination: Pagination | None = None) -> PaginatedResult[Repository]:
        """List all repositories with pagination."""
        ...

    async def save(self, repository: Repository) -> Repository:
        """Save repository (create or update)."""
        ...

    async def delete(self, repo_id: int) -> bool:
        """Delete repository by ID."""
        ...


@runtime_checkable
class WorkflowRepository(Protocol):
    """Repository interface for Workflow entities."""

    async def get_by_id(self, workflow_id: int) -> Workflow | None:
        """Get workflow by ID."""
        ...

    async def get_by_github_id(self, github_id: int) -> Workflow | None:
        """Get workflow by GitHub ID."""
        ...

    async def list_by_repository(self, repo_id: int) -> list[Workflow]:
        """List workflows for a repository."""
        ...

    async def list_all(self, pagination: Pagination | None = None) -> PaginatedResult[Workflow]:
        """List all workflows with pagination."""
        ...

    async def save(self, workflow: Workflow) -> Workflow:
        """Save workflow (create or update)."""
        ...


@runtime_checkable
class WorkflowRunRepository(Protocol):
    """Repository interface for WorkflowRun entities."""

    async def get_by_id(self, run_id: int) -> WorkflowRun | None:
        """Get run by ID."""
        ...

    async def get_by_github_id(self, github_id: int) -> WorkflowRun | None:
        """Get run by GitHub ID."""
        ...

    async def list_by_workflow(
        self,
        workflow_id: int,
        pagination: Pagination | None = None,
    ) -> PaginatedResult[WorkflowRun]:
        """List runs for a workflow."""
        ...

    async def list_recent_failures(
        self,
        limit: int = 10,
        repository_ids: list[int] | None = None,
    ) -> list[WorkflowRun]:
        """List recent failed runs."""
        ...

    async def list_in_time_range(
        self,
        time_range: TimeRange,
        repository_ids: list[int] | None = None,
    ) -> list[WorkflowRun]:
        """List runs within time range."""
        ...

    async def count_by_status(
        self,
        time_range: TimeRange,
        repository_ids: list[int] | None = None,
    ) -> dict[str, int]:
        """Count runs by status/conclusion in time range."""
        ...

    async def save(self, run: WorkflowRun) -> WorkflowRun:
        """Save run (create or update)."""
        ...


@runtime_checkable
class JobRepository(Protocol):
    """Repository interface for Job entities."""

    async def get_by_id(self, job_id: int) -> Job | None:
        """Get job by ID."""
        ...

    async def get_by_github_id(self, github_id: int) -> Job | None:
        """Get job by GitHub ID."""
        ...

    async def list_by_run(self, run_id: int) -> list[Job]:
        """List jobs for a run."""
        ...

    async def list_failed_by_run(self, run_id: int) -> list[Job]:
        """List failed jobs for a run."""
        ...

    async def save(self, job: Job) -> Job:
        """Save job (create or update)."""
        ...


@runtime_checkable
class LogRepository(Protocol):
    """Repository interface for Log entities."""

    async def get_by_id(self, log_id: int) -> Log | None:
        """Get log by ID."""
        ...

    async def get_by_job_id(self, job_id: int) -> Log | None:
        """Get log for a job."""
        ...

    async def get_by_content_hash(self, content_hash: str) -> Log | None:
        """Get log by content hash."""
        ...

    async def list_without_embedding(self, limit: int = 100) -> list[Log]:
        """List logs that don't have embeddings yet."""
        ...

    async def save(self, log: Log) -> Log:
        """Save log (create or update)."""
        ...

    async def search_semantic(
        self,
        embedding: list[float],
        limit: int = 10,
        min_score: float = 0.5,
    ) -> list[tuple[Log, float]]:
        """Search logs by embedding similarity."""
        ...

    async def search_text(self, query: str, limit: int = 20) -> list[Log]:
        """Search logs by full-text search."""
        ...


@runtime_checkable
class ErrorAnalysisRepository(Protocol):
    """Repository interface for ErrorAnalysis entities."""

    async def get_by_id(self, analysis_id: int) -> ErrorAnalysis | None:
        """Get analysis by ID."""
        ...

    async def get_by_log_id(self, log_id: int) -> ErrorAnalysis | None:
        """Get analysis for a log."""
        ...

    async def list_recent(
        self,
        limit: int = 10,
        high_confidence_only: bool = False,
    ) -> list[ErrorAnalysis]:
        """List recent analyses."""
        ...

    async def save(self, analysis: ErrorAnalysis) -> ErrorAnalysis:
        """Save analysis (create or update)."""
        ...


@runtime_checkable
class TestResultRepository(Protocol):
    """Repository interface for TestResult entities."""

    async def get_by_id(self, result_id: int) -> TestResult | None:
        """Get test result by ID."""
        ...

    async def get_by_log_id(self, log_id: int) -> TestResult | None:
        """Get test result for a log."""
        ...

    async def list_by_framework(
        self,
        framework: str,
        pagination: Pagination | None = None,
    ) -> PaginatedResult[TestResult]:
        """List test results by framework."""
        ...

    async def save(self, result: TestResult) -> TestResult:
        """Save test result (create or update)."""
        ...


@runtime_checkable
class NotificationRepository(Protocol):
    """Repository interface for Notification entities."""

    async def get_by_id(self, notification_id: int) -> Notification | None:
        """Get notification by ID."""
        ...

    async def list_pending(self, limit: int = 100) -> list[Notification]:
        """List pending notifications."""
        ...

    async def list_failed(self, limit: int = 100) -> list[Notification]:
        """List failed notifications for retry."""
        ...

    async def save(self, notification: Notification) -> Notification:
        """Save notification (create or update)."""
        ...


@runtime_checkable
class TrendRepository(Protocol):
    """Repository interface for trend data aggregation."""

    async def get_trend(
        self,
        metric_type: MetricType,
        period: TrendPeriod,
        time_range: TimeRange,
        repository_ids: list[int] | None = None,
    ) -> TrendData:
        """Get trend data for a metric."""
        ...

    async def get_success_rate_over_time(
        self,
        period: TrendPeriod,
        time_range: TimeRange,
        repository_ids: list[int] | None = None,
    ) -> TrendData:
        """Get success rate trend."""
        ...

    async def get_failure_counts_by_workflow(
        self,
        time_range: TimeRange,
        limit: int = 10,
    ) -> list[tuple[int, str, int]]:
        """Get failure counts grouped by workflow. Returns (workflow_id, name, count)."""
        ...

    async def get_average_duration_over_time(
        self,
        period: TrendPeriod,
        time_range: TimeRange,
        workflow_ids: list[int] | None = None,
    ) -> TrendData:
        """Get average duration trend."""
        ...
