"""ErrorAnalysis model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.log import Log


class ErrorAnalysis(Base, TimestampMixin):
    """LLM-generated error analysis."""

    __tablename__ = "error_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    log_id: Mapped[int] = mapped_column(ForeignKey("logs.id"), unique=True, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text)
    error_summary: Mapped[str | None] = mapped_column(Text)
    suggested_fixes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    prevention_tips: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    related_documentation: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    llm_model: Mapped[str | None] = mapped_column(String(100))
    llm_tokens_used: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    analyzed_at: Mapped[datetime | None] = mapped_column()

    # Relationships
    log: Mapped[Log] = relationship(back_populates="error_analyses")
