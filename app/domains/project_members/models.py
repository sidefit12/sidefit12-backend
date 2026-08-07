"""프로젝트 팀원 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectMember(Base):
    """프로젝트에 합류한 사용자와 역할을 저장한다."""

    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uk_project_members_user"),
        UniqueConstraint("project_application_id", name="uk_project_members_application"),
        ForeignKeyConstraint(
            ["project_id", "project_position_id"],
            ["project_positions.project_id", "project_positions.project_position_id"],
            name="fk_members_positions",
            ondelete="RESTRICT",
        ),
        CheckConstraint("member_type IN ('OWNER','MEMBER')", name="ck_project_members_type"),
        CheckConstraint(
            "(member_type = 'OWNER' AND project_position_id IS NULL) OR "
            "(member_type = 'MEMBER' AND project_position_id IS NOT NULL)",
            name="ck_project_members_position_by_type",
        ),
        CheckConstraint(
            "member_status IN ('ACTIVE','LEFT','REMOVED')", name="ck_project_members_status"
        ),
        CheckConstraint(
            "(member_status = 'ACTIVE' AND left_at IS NULL) OR (member_status <> 'ACTIVE' AND left_at IS NOT NULL)",
            name="ck_project_members_end_time",
        ),
    )
    project_member_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    project_position_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    project_application_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_applications.project_application_id", ondelete="SET NULL"),
        nullable=True,
    )
    member_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'MEMBER'")
    )
    member_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'ACTIVE'")
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
