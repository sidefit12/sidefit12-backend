"""프로젝트 지원 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectApplication(Base):
    """사용자의 프로젝트 포지션 지원 내역을 저장한다."""

    __tablename__ = "project_applications"
    __table_args__ = (
        UniqueConstraint("project_id", "applicant_user_id", name="uk_project_applications_user"),
        ForeignKeyConstraint(
            ["project_id", "project_position_id"],
            ["project_positions.project_id", "project_positions.project_position_id"],
            name="fk_applications_positions",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "application_status IN ('PENDING','ACCEPTED','REJECTED','CANCELED')",
            name="ck_project_applications_status",
        ),
        CheckConstraint(
            "(application_status = 'PENDING' AND reviewed_at IS NULL) "
            "OR application_status IN ('ACCEPTED','REJECTED','CANCELED')",
            name="ck_project_applications_review",
        ),
    )
    project_application_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    project_position_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    applicant_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    application_message: Mapped[str | None] = mapped_column(Text)
    application_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'PENDING'")
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(String(500))
