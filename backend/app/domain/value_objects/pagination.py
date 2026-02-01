"""Pagination value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Pagination:
    """Immutable value object for pagination parameters."""

    page: int = 1
    per_page: int = 20
    max_per_page: int = 100

    def __post_init__(self) -> None:
        """Validate pagination parameters."""
        if self.page < 1:
            object.__setattr__(self, "page", 1)
        if self.per_page < 1:
            object.__setattr__(self, "per_page", 1)
        if self.per_page > self.max_per_page:
            object.__setattr__(self, "per_page", self.max_per_page)

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Get limit (same as per_page)."""
        return self.per_page

    @classmethod
    def first_page(cls, per_page: int = 20) -> Pagination:
        """Create pagination for first page."""
        return cls(page=1, per_page=per_page)

    def next_page(self) -> Pagination:
        """Get pagination for next page."""
        return Pagination(page=self.page + 1, per_page=self.per_page)

    def prev_page(self) -> Pagination:
        """Get pagination for previous page."""
        if self.page <= 1:
            return self
        return Pagination(page=self.page - 1, per_page=self.per_page)


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """Immutable value object for paginated results."""

    items: list[T]
    total: int
    page: int
    per_page: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    @property
    def is_empty(self) -> bool:
        """Check if result is empty."""
        return len(self.items) == 0

    @classmethod
    def empty(cls, page: int = 1, per_page: int = 20) -> PaginatedResult[T]:
        """Create empty paginated result."""
        return cls(items=[], total=0, page=page, per_page=per_page)
