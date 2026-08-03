"""프로젝트 모집 포지션 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectPosition(Base):
    """프로젝트에서 모집하는 역할과 인원 정보를 저장한다."""

    __tablename__ = "project_positions"
    __table_args__ = (
        UniqueConstraint("project_id", "role_id", name="uk_project_positions_role"),
        UniqueConstraint(
            "project_id", "project_position_id", name="uk_project_positions_project_position"
        ),
        CheckConstraint("required_count > 0", name="ck_project_positions_count"),
        CheckConstraint(
            "required_level IS NULL OR required_level IN ('BEGINNER','INTERMEDIATE','ADVANCED')",
            name="ck_project_positions_level",
        ),
        CheckConstraint("position_status IN ('OPEN','CLOSED')", name="ck_project_positions_status"),
    )
    project_position_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False
    )
    position_title: Mapped[str] = mapped_column(String(100), nullable=False)
    responsibilities: Mapped[str | None] = mapped_column(Text)
    required_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    required_level: Mapped[str | None] = mapped_column(String(20))
    position_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'OPEN'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
