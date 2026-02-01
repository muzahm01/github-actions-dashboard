"""WorkflowRun domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

RunStatus = Literal["queued", "in_progress", "completed", "waiting"]
RunConclusion = Literal[
    "success", "failure", "cancelled", "skipped", "timed_out", "action_required", None
]


@dataclass
class WorkflowRun:
    """Domain entity representing a GitHub Actions workflow run."""

    id: int
    github_id: int
    workflow_id: int
    run_number: int
    name: str
    display_title: str
    status: RunStatus
    conclusion: RunConclusion = None
    head_branch: str = ""
    head_sha: str = ""
    event: str = "push"
    actor: str = ""
    run_attempt: int = 1
    html_url: str = ""
    run_started_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        github_id: int,
        workflow_id: int,
        run_number: int,
        name: str,
        display_title: str,
        status: RunStatus = "queued",
        head_branch: str = "",
        head_sha: str = "",
        event: str = "push",
        actor: str = "",
    ) -> WorkflowRun:
        """Create a new workflow run entity."""
        now = datetime.utcnow()
        return cls(
            id=0,
            github_id=github_id,
            workflow_id=workflow_id,
            run_number=run_number,
            name=name,
            display_title=display_title,
            status=status,
            head_branch=head_branch,
            head_sha=head_sha,
            event=event,
            actor=actor,
            created_at=now,
            updated_at=now,
        )

    def is_completed(self) -> bool:
        """Check if run is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if run failed."""
        return self.conclusion == "failure"

    def is_successful(self) -> bool:
        """Check if run was successful."""
        return self.conclusion == "success"

    def complete(self, conclusion: RunConclusion) -> None:
        """Mark run as completed with given conclusion."""
        self.status = "completed"
        self.conclusion = conclusion
        self.updated_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> int | None:
        """Calculate run duration in seconds."""
        if not self.run_started_at or not self.is_completed():
            return None
        return int((self.updated_at - self.run_started_at).total_seconds())
