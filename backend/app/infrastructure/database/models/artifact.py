"""Artifact model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.workflow_run import WorkflowRun


class Artifact(Base, TimestampMixin):
    """Workflow artifacts."""

    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False, index=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    expired: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column()
    archive_download_url: Mapped[str | None] = mapped_column(Text)

    # Relationships
    run: Mapped[WorkflowRun] = relationship(back_populates="artifacts")
