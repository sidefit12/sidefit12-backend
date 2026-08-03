"""프로젝트 북마크 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProjectBookmark(Base):
    __tablename__ = "project_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uk_project_bookmarks"),)
    project_bookmark_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
