"""파일 ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class File(Base):
    """업로드 파일의 저장소 정보와 공개 정책을 저장한다."""

    __tablename__ = "files"
    __table_args__ = (
        CheckConstraint("file_size >= 0", name="ck_files_size"),
        CheckConstraint(
            "file_category IN ('PROFILE_IMAGE','PUBLIC_MATERIAL')",
            name="ck_files_category",
        ),
        CheckConstraint("visibility IN ('PUBLIC','PRIVATE')", name="ck_files_visibility"),
        CheckConstraint("file_status IN ('UPLOADING','ACTIVE','DELETED')", name="ck_files_status"),
        CheckConstraint(
            "download_allowed = FALSE OR visibility = 'PUBLIC'",
            name="ck_files_download_policy",
        ),
    )

    file_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    uploader_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_category: Mapped[str] = mapped_column(String(30), nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'PRIVATE'")
    )
    preview_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("TRUE")
    )
    download_allowed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    file_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'ACTIVE'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
