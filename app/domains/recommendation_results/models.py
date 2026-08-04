"""추천 결과 ORM 모델."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecommendationResult(Base):
    """사용자별 프로젝트 추천 점수와 버전을 저장한다."""

    __tablename__ = "recommendation_results"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "project_id", "recommendation_version", name="uk_recommendation_results"
        ),
        CheckConstraint("rule_score BETWEEN 0 AND 1", name="ck_recommendation_results_rule"),
        CheckConstraint(
            "semantic_score IS NULL OR semantic_score BETWEEN 0 AND 1",
            name="ck_recommendation_results_semantic",
        ),
        CheckConstraint("final_score BETWEEN 0 AND 1", name="ck_recommendation_results_final"),
        Index("idx_recommendations_user_score", "user_id", text("final_score DESC")),
    )

    recommendation_result_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False
    )
    rule_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    semantic_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    final_score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    recommendation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
