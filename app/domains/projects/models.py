"""프로젝트와 모집 관련 SQLAlchemy ORM 모델."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("work_type IN ('ONLINE','OFFLINE','HYBRID')", name="ck_projects_work_type"),
        CheckConstraint(
            "recruitment_status IN ('DRAFT','RECRUITING','CLOSED')",
            name="ck_projects_recruitment_status",
        ),
        CheckConstraint(
            "project_status IN ('PREPARING','IN_PROGRESS','COMPLETED','CANCELED')",
            name="ck_projects_project_status",
        ),
        CheckConstraint("visibility IN ('PUBLIC','PRIVATE')", name="ck_projects_visibility"),
        CheckConstraint(
            "expected_end_date IS NULL OR expected_start_date IS NULL OR expected_end_date >= expected_start_date",
            name="ck_projects_date_range",
        ),
        CheckConstraint(
            "weekly_hours IS NULL OR weekly_hours BETWEEN 1 AND 168",
            name="ck_projects_weekly_hours",
        ),
        CheckConstraint("view_count >= 0", name="ck_projects_view_count"),
        CheckConstraint(
            "(deleted_at IS NULL AND deletion_reason IS NULL) OR deleted_at IS NOT NULL",
            name="ck_projects_deletion",
        ),
    )

    project_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    work_type: Mapped[str] = mapped_column(String(20), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))
    expected_start_date: Mapped[date | None] = mapped_column(Date)
    expected_end_date: Mapped[date | None] = mapped_column(Date)
    weekly_hours: Mapped[int | None] = mapped_column(SmallInteger)
    recruitment_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recruitment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'DRAFT'")
    )
    project_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'PREPARING'")
    )
    visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'PUBLIC'")
    )
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    normalized_text: Mapped[str | None] = mapped_column(Text)
    embedding_version: Mapped[str | None] = mapped_column(String(50))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL")
    )
    deletion_reason: Mapped[str | None] = mapped_column(String(500))


class ProjectTopic(Base):
    __tablename__ = "project_topics"
    __table_args__ = (UniqueConstraint("project_id", "topic_id", name="uk_project_topics"),)
    project_topic_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.topic_id", ondelete="RESTRICT"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class ProjectTechStack(Base):
    __tablename__ = "project_tech_stacks"
    __table_args__ = (
        UniqueConstraint("project_id", "tech_stack_id", name="uk_project_tech_stacks"),
        CheckConstraint(
            "requirement_type IN ('REQUIRED','PREFERRED')", name="ck_project_tech_stacks_type"
        ),
        CheckConstraint(
            "required_level IS NULL OR required_level IN ('BEGINNER','INTERMEDIATE','ADVANCED')",
            name="ck_project_tech_stacks_level",
        ),
    )
    project_tech_stack_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    tech_stack_id: Mapped[int] = mapped_column(
        ForeignKey("tech_stacks.tech_stack_id", ondelete="RESTRICT"), nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    required_level: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
