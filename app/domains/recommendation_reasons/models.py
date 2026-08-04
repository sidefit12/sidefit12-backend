"""추천 이유 ORM 모델."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecommendationReason(Base):
    """추천 점수에 기여한 구조화된 이유를 저장한다."""

    __tablename__ = "recommendation_reasons"
    __table_args__ = (
        CheckConstraint(
            "reason_type IN ('MATCHED_TOPIC','MATCHED_TECH_STACK','MATCHED_ROLE','MATCHED_WORK_TYPE','SEMANTIC_SIMILARITY','COLD_START')",
            name="ck_recommendation_reasons_type",
        ),
        CheckConstraint(
            "contribution_score IS NULL OR contribution_score BETWEEN 0 AND 1",
            name="ck_recommendation_reasons_score",
        ),
    )

    recommendation_reason_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    recommendation_result_id: Mapped[int] = mapped_column(
        ForeignKey("recommendation_results.recommendation_result_id", ondelete="CASCADE"),
        nullable=False,
    )
    reason_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(30))
    reference_id: Mapped[int | None] = mapped_column(BigInteger)
    reason_text: Mapped[str] = mapped_column(String(500), nullable=False)
    contribution_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
