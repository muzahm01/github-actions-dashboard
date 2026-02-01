"""Workflow-related domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from app.domain.events.base import DomainEvent


@dataclass
class WorkflowRunStarted(DomainEvent):
    """Event emitted when a workflow run starts."""

    run_id: int = 0
    workflow_id: int = 0
    repository_id: int = 0
    github_run_id: int = 0
    branch: str = ""
    commit_sha: str = ""
    actor: str = ""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "workflow_run.started"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "repository_id": self.repository_id,
            "github_run_id": self.github_run_id,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "actor": self.actor,
        }


@dataclass
class WorkflowRunCompleted(DomainEvent):
    """Event emitted when a workflow run completes."""

    run_id: int = 0
    workflow_id: int = 0
    repository_id: int = 0
    conclusion: str = ""
    duration_seconds: int = 0
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "workflow_run.completed"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "repository_id": self.repository_id,
            "conclusion": self.conclusion,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class WorkflowRunFailed(DomainEvent):
    """Event emitted when a workflow run fails."""

    run_id: int = 0
    workflow_id: int = 0
    repository_id: int = 0
    repository_name: str = ""
    workflow_name: str = ""
    branch: str = ""
    commit_sha: str = ""
    actor: str = ""
    run_url: str = ""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "workflow_run.failed"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "repository_id": self.repository_id,
            "repository_name": self.repository_name,
            "workflow_name": self.workflow_name,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "actor": self.actor,
            "run_url": self.run_url,
        }


@dataclass
class JobCompleted(DomainEvent):
    """Event emitted when a job completes."""

    job_id: int = 0
    run_id: int = 0
    job_name: str = ""
    conclusion: str = ""
    duration_seconds: int = 0
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "job.completed"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "job_id": self.job_id,
            "run_id": self.run_id,
            "job_name": self.job_name,
            "conclusion": self.conclusion,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class JobFailed(DomainEvent):
    """Event emitted when a job fails."""

    job_id: int = 0
    run_id: int = 0
    job_name: str = ""
    error_message: str = ""
    log_id: int | None = None
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_type(self) -> str:
        """Return event type identifier."""
        return "job.failed"

    def _payload_dict(self) -> dict:
        """Return event payload."""
        return {
            "job_id": self.job_id,
            "run_id": self.run_id,
            "job_name": self.job_name,
            "error_message": self.error_message,
            "log_id": self.log_id,
        }
