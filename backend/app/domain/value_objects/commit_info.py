"""CommitInfo value object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CommitInfo:
    """Immutable value object representing commit information."""

    sha: str
    message: str
    author: str
    author_email: str = ""
    timestamp: datetime | None = None

    @classmethod
    def from_github(cls, data: dict) -> CommitInfo:
        """Create from GitHub API response."""
        commit_data = data.get("commit", data)
        author_data = commit_data.get("author", {})

        timestamp = None
        if date_str := author_data.get("date"):
            try:
                timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            sha=data.get("sha", ""),
            message=commit_data.get("message", ""),
            author=author_data.get("name", ""),
            author_email=author_data.get("email", ""),
            timestamp=timestamp,
        )

    @property
    def short_sha(self) -> str:
        """Get abbreviated SHA (first 7 characters)."""
        return self.sha[:7] if self.sha else ""

    @property
    def first_line(self) -> str:
        """Get first line of commit message."""
        return self.message.split("\n")[0] if self.message else ""

    def __str__(self) -> str:
        """String representation."""
        return f"{self.short_sha}: {self.first_line}"
