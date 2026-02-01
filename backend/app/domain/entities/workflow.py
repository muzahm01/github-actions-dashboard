"""Workflow domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Workflow:
    """Domain entity representing a GitHub Actions workflow."""

    id: int
    github_id: int
    repository_id: int
    name: str
    path: str
    state: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        github_id: int,
        repository_id: int,
        name: str,
        path: str,
        state: str = "active",
    ) -> Workflow:
        """Create a new workflow entity."""
        now = datetime.utcnow()
        return cls(
            id=0,
            github_id=github_id,
            repository_id=repository_id,
            name=name,
            path=path,
            state=state,
            created_at=now,
            updated_at=now,
        )

    def is_active(self) -> bool:
        """Check if workflow is active."""
        return self.state == "active"

    def disable(self) -> None:
        """Disable the workflow."""
        self.state = "disabled"
        self.updated_at = datetime.utcnow()

    def enable(self) -> None:
        """Enable the workflow."""
        self.state = "active"
        self.updated_at = datetime.utcnow()
