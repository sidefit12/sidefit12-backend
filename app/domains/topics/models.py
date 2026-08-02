"""관심 토픽 기준정보 ORM 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Topic(Base):
    """사용자와 프로젝트가 선택할 수 있는 관심 토픽."""

    __tablename__ = "topics"

    topic_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    topic_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    topic_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
