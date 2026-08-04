"""추천 이유 repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.recommendation_reasons.models import RecommendationReason


class RecommendationReasonRepository:
    @staticmethod
    def list_by_result(db: Session, result_id: int) -> list[RecommendationReason]:
        return list(
            db.scalars(
                select(RecommendationReason)
                .where(RecommendationReason.recommendation_result_id == result_id)
                .order_by(
                    RecommendationReason.contribution_score.desc(),
                    RecommendationReason.recommendation_reason_id,
                )
            ).all()
        )

    @staticmethod
    def add_all(db: Session, reasons: list[RecommendationReason]) -> None:
        db.add_all(reasons)
