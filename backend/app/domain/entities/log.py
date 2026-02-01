"""Log domain entity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Log:
    """Domain entity representing job logs."""

    id: int
    job_id: int
    content: str
    content_hash: str = ""
    size_bytes: int = 0
    has_embedding: bool = False
    parsed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, job_id: int, content: str) -> Log:
        """Create a new log entity with computed hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        now = datetime.utcnow()
        return cls(
            id=0,
            job_id=job_id,
            content=content,
            content_hash=content_hash,
            size_bytes=len(content.encode()),
            created_at=now,
            updated_at=now,
        )

    def update_content(self, content: str) -> None:
        """Update log content and recompute hash."""
        self.content = content
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.size_bytes = len(content.encode())
        self.updated_at = datetime.utcnow()

    def mark_parsed(self) -> None:
        """Mark log as parsed."""
        self.parsed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_embedded(self) -> None:
        """Mark that embedding was generated."""
        self.has_embedding = True
        self.updated_at = datetime.utcnow()

    def is_parsed(self) -> bool:
        """Check if log has been parsed."""
        return self.parsed_at is not None

    def truncate(self, max_length: int = 50000) -> str:
        """Get truncated content for display or analysis."""
        if len(self.content) <= max_length:
            return self.content
        half = max_length // 2
        return self.content[:half] + "\n\n... [truncated] ...\n\n" + self.content[-half:]
