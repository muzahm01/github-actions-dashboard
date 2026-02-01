"""Repository domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Repository:
    """Domain entity representing a GitHub repository."""

    id: int
    github_id: int
    name: str
    full_name: str
    owner: str
    default_branch: str
    is_active: bool = True
    webhook_configured: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        github_id: int,
        name: str,
        full_name: str,
        owner: str,
        default_branch: str = "main",
    ) -> Repository:
        """Create a new repository entity."""
        now = datetime.utcnow()
        return cls(
            id=0,  # Will be assigned by persistence layer
            github_id=github_id,
            name=name,
            full_name=full_name,
            owner=owner,
            default_branch=default_branch,
            is_active=True,
            webhook_configured=False,
            created_at=now,
            updated_at=now,
        )

    def activate(self) -> None:
        """Activate repository monitoring."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate repository monitoring."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def mark_webhook_configured(self) -> None:
        """Mark webhook as configured."""
        self.webhook_configured = True
        self.updated_at = datetime.utcnow()
