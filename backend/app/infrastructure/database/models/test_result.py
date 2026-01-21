"""TestResult model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.log import Log


class TestResult(Base, TimestampMixin):
    """Parsed test results from logs."""

    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    log_id: Mapped[int] = mapped_column(ForeignKey("logs.id"), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, nullable=False)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    raw_output: Mapped[str | None] = mapped_column(Text)
    parsed_failures: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    log: Mapped[Log] = relationship(back_populates="test_results")
