"""역할 기준정보 ORM 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Role(Base):
    """사용자 희망 역할과 프로젝트 포지션에서 사용하는 역할."""

    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
