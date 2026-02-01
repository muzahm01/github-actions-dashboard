"""Job domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

JobStatus = Literal["queued", "in_progress", "completed", "waiting"]
JobConclusion = Literal[
    "success", "failure", "cancelled", "skipped", "timed_out", "action_required", None
]


@dataclass
class Job:
    """Domain entity representing a GitHub Actions job."""

    id: int
    github_id: int
    run_id: int
    name: str
    status: JobStatus
    conclusion: JobConclusion = None
    runner_name: str = ""
    runner_group_name: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    html_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        github_id: int,
        run_id: int,
        name: str,
        status: JobStatus = "queued",
    ) -> Job:
        """Create a new job entity."""
        now = datetime.utcnow()
        return cls(
            id=0,
            github_id=github_id,
            run_id=run_id,
            name=name,
            status=status,
            created_at=now,
            updated_at=now,
        )

    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.conclusion == "failure"

    def is_successful(self) -> bool:
        """Check if job was successful."""
        return self.conclusion == "success"

    def complete(self, conclusion: JobConclusion, completed_at: datetime | None = None) -> None:
        """Mark job as completed."""
        self.status = "completed"
        self.conclusion = conclusion
        self.completed_at = completed_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> int | None:
        """Calculate job duration in seconds."""
        if not self.started_at or not self.completed_at:
            return None
        return int((self.completed_at - self.started_at).total_seconds())
