"""중복 생성 방지 요청 SQLAlchemy ORM 모델."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IdempotencyRequest(Base):
    """사용자별 멱등 키와 생성 결과를 저장한다."""

    __tablename__ = "idempotency_requests"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uk_idempotency_requests_user_key"),
    )
    idempotency_request_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
