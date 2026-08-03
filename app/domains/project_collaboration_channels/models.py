"""프로젝트 협업 채널 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectCollaborationChannel(Base):
    """프로젝트에서 사용하는 외부 협업 채널 정보를 저장한다."""

    __tablename__ = "project_collaboration_channels"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "channel_type", "channel_url", name="uk_project_collaboration_channels"
        ),
        CheckConstraint(
            "channel_type IN ('DISCORD','KAKAO_OPEN_CHAT','SLACK','NOTION','OTHER')",
            name="ck_collaboration_channels_type",
        ),
    )
    project_collaboration_channel_id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    registered_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
