"""프로젝트 팀원 이벤트 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectMemberEvent(Base):
    """팀원의 합류·탈퇴·퇴출·복구 이력을 저장한다."""

    __tablename__ = "project_member_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('JOINED','LEFT','REMOVED','RESTORED')",
            name="ck_project_member_events_type",
        ),
        CheckConstraint(
            "event_type <> 'REMOVED' OR length(trim(reason)) >= 10",
            name="ck_project_member_events_reason",
        ),
    )
    project_member_event_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_member_id: Mapped[int] = mapped_column(
        ForeignKey("project_members.project_member_id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL")
    )
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
