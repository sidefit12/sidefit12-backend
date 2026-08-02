"""사용자 ORM 모델을 정의하는 모듈."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """사용자 테이블과 매핑되는 SQLAlchemy ORM 모델."""

    __tablename__ = "users"

    __table_args__ = (
        UniqueConstraint(
            "email",
            name="uk_users_email",
        ),
        UniqueConstraint(
            "nickname",
            name="uk_users_nickname",
        ),
        CheckConstraint(
            "user_status IN "
            "('PENDING', 'ACTIVE', 'SUSPENDED', 'WITHDRAWN')",
            name="ck_users_status",
        ),
        CheckConstraint(
            "system_role IN ('USER', 'ADMIN')",
            name="ck_users_system_role",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    user_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'PENDING'"),
    )

    system_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'USER'"),
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )