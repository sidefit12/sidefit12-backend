"""이메일 인증 ORM 모델."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmailVerification(Base):
    """이메일 인증 코드와 일회성 인증 토큰을 저장한다."""

    __tablename__ = "email_verifications"
    __table_args__ = (
        CheckConstraint(
            "verification_type IN ('SIGN_UP', 'PASSWORD_RESET', 'EMAIL_CHANGE')",
            name="ck_email_verifications_type",
        ),
        CheckConstraint("attempt_count >= 0", name="ck_email_verifications_attempt"),
    )

    email_verification_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_type: Mapped[str] = mapped_column(String(30), nullable=False)
    verification_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
