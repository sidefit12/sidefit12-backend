"""사용자 프로필과 프로필 소유 중간 테이블 ORM 모델."""

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
from app.domains.files.models import File


class UserProfile(Base):
    """사용자의 소개와 프로젝트 참여 선호 정보를 저장한다."""

    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            "preferred_work_type IS NULL OR preferred_work_type IN ('ONLINE','OFFLINE','HYBRID')",
            name="ck_user_profiles_work_type",
        ),
        CheckConstraint(
            "available_end_date IS NULL OR available_start_date IS NULL "
            "OR available_end_date >= available_start_date",
            name="ck_user_profiles_date_range",
        ),
        CheckConstraint(
            "available_hours_per_week IS NULL OR available_hours_per_week BETWEEN 1 AND 168",
            name="ck_user_profiles_hours",
        ),
        CheckConstraint(
            "profile_image_file_id IS NULL OR public_material_file_id IS NULL "
            "OR profile_image_file_id <> public_material_file_id",
            name="ck_user_profiles_distinct_files",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    introduction: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_link_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    profile_image_file_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(File.file_id, ondelete="SET NULL"), nullable=True
    )
    public_material_file_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(File.file_id, ondelete="SET NULL"), nullable=True
    )
    career_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_work_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    available_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    available_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    available_hours_per_week: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class UserTopic(Base):
    """사용자가 선택한 관심 토픽 관계."""

    __tablename__ = "user_topics"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uk_user_topics"),
        CheckConstraint("interest_level BETWEEN 1 AND 5", name="ck_user_topics_interest_level"),
        CheckConstraint("priority >= 0", name="ck_user_topics_priority"),
    )

    user_topic_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.topic_id", ondelete="RESTRICT"), nullable=False
    )
    interest_level: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("3")
    )
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class UserTechStack(Base):
    """사용자가 보유하거나 학습 중인 기술 스택 관계."""

    __tablename__ = "user_tech_stacks"
    __table_args__ = (
        UniqueConstraint("user_id", "tech_stack_id", name="uk_user_tech_stacks"),
        CheckConstraint(
            "proficiency_level IN ('LEARNING','BEGINNER','INTERMEDIATE','ADVANCED')",
            name="ck_user_tech_stacks_level",
        ),
        CheckConstraint("experience_months >= 0", name="ck_user_tech_stacks_months"),
    )

    user_tech_stack_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    tech_stack_id: Mapped[int] = mapped_column(
        ForeignKey("tech_stacks.tech_stack_id", ondelete="RESTRICT"), nullable=False
    )
    proficiency_level: Mapped[str] = mapped_column(String(20), nullable=False)
    experience_months: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    is_learning: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class UserRole(Base):
    """사용자가 프로젝트에서 희망하는 역할 관계."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uk_user_roles"),
        CheckConstraint("priority >= 1", name="ck_user_roles_priority"),
        CheckConstraint(
            "experience_level IS NULL OR experience_level IN ('BEGINNER','INTERMEDIATE','ADVANCED')",
            name="ck_user_roles_level",
        ),
    )

    user_role_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False
    )
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("1"))
    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
