"""신고 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("target_type IN ('USER','PROJECT')", name="ck_reports_target_type"),
        CheckConstraint(
            "report_status IN ('PENDING','IN_REVIEW','RESOLVED','REJECTED')",
            name="ck_reports_status",
        ),
        CheckConstraint(
            "(target_type = 'USER' AND target_user_id IS NOT NULL AND target_project_id IS NULL) OR (target_type = 'PROJECT' AND target_project_id IS NOT NULL AND target_user_id IS NULL)",
            name="ck_reports_target",
        ),
        Index("idx_reports_status_created", "report_status", "created_at"),
    )
    report_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    reporter_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT")
    )
    target_project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.project_id", ondelete="RESTRICT")
    )
    reason_type: Mapped[str] = mapped_column(String(30), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    report_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="PENDING")
    handled_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL")
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
