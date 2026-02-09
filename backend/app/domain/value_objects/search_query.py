"""Search query value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal


class SearchType(str, Enum):
    """Type of search to perform."""

    SEMANTIC = "semantic"  # Vector similarity search
    TEXT = "text"  # Full-text search
    HYBRID = "hybrid"  # Combined semantic + text search


@dataclass(frozen=True)
class SearchQuery:
    """Immutable value object for search parameters."""

    query: str
    search_type: SearchType = SearchType.SEMANTIC
    limit: int = 20
    min_score: float = 0.5
    repository_ids: tuple[int, ...] = field(default_factory=tuple)
    workflow_ids: tuple[int, ...] = field(default_factory=tuple)
    status_filter: tuple[str, ...] = field(default_factory=tuple)
    date_from: datetime | None = None
    date_to: datetime | None = None

    def __post_init__(self) -> None:
        """Validate search query."""
        if self.limit < 1:
            object.__setattr__(self, "limit", 1)
        if self.limit > 100:
            object.__setattr__(self, "limit", 100)
        if self.min_score < 0:
            object.__setattr__(self, "min_score", 0.0)
        if self.min_score > 1:
            object.__setattr__(self, "min_score", 1.0)

    @classmethod
    def semantic(cls, query: str, limit: int = 20) -> SearchQuery:
        """Create semantic search query."""
        return cls(query=query, search_type=SearchType.SEMANTIC, limit=limit)

    @classmethod
    def text(cls, query: str, limit: int = 20) -> SearchQuery:
        """Create text search query."""
        return cls(query=query, search_type=SearchType.TEXT, limit=limit)

    @classmethod
    def hybrid(cls, query: str, limit: int = 20) -> SearchQuery:
        """Create hybrid search query."""
        return cls(query=query, search_type=SearchType.HYBRID, limit=limit)

    def with_repository_filter(self, *repo_ids: int) -> SearchQuery:
        """Create new query with repository filter."""
        return SearchQuery(
            query=self.query,
            search_type=self.search_type,
            limit=self.limit,
            min_score=self.min_score,
            repository_ids=tuple(repo_ids),
            workflow_ids=self.workflow_ids,
            status_filter=self.status_filter,
            date_from=self.date_from,
            date_to=self.date_to,
        )


ResultType = Literal["workflow", "run", "job", "log", "error_analysis"]


@dataclass(frozen=True)
class SearchResult:
    """Immutable value object for search result."""

    id: int
    result_type: ResultType
    title: str
    description: str = ""
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_log(
        cls,
        log_id: int,
        job_name: str,
        content_preview: str,
        score: float = 0.0,
        **metadata: object,
    ) -> SearchResult:
        """Create search result from log match."""
        return cls(
            id=log_id,
            result_type="log",
            title=f"Log: {job_name}",
            description=content_preview[:200],
            score=score,
            metadata=dict(metadata),
        )

    @classmethod
    def from_workflow(
        cls,
        workflow_id: int,
        name: str,
        path: str,
        score: float = 0.0,
        **metadata: object,
    ) -> SearchResult:
        """Create search result from workflow match."""
        return cls(
            id=workflow_id,
            result_type="workflow",
            title=name,
            description=path,
            score=score,
            metadata=dict(metadata),
        )

    def is_relevant(self, threshold: float = 0.5) -> bool:
        """Check if result is relevant based on score."""
        return self.score >= threshold
