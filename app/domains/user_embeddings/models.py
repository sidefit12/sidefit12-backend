"""사용자 추천 임베딩 ORM 모델."""

from datetime import datetime

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserEmbedding(Base):
    """사용자 프로필을 벡터화한 결과와 원문 버전을 저장한다."""

    __tablename__ = "user_embeddings"
    __table_args__ = (
        UniqueConstraint("user_id", "embedding_version", name="uk_user_embeddings_version"),
    )

    user_embedding_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(768), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(50), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
