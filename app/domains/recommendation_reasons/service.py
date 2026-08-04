"""추천 이유 서비스."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.recommendation_reasons.models import RecommendationReason
from app.domains.recommendation_reasons.repository import RecommendationReasonRepository


class RecommendationReasonService:
    @staticmethod
    def list_by_result(db: Session, result_id: int) -> list[RecommendationReason]:
        return RecommendationReasonRepository.list_by_result(db, result_id)

    @staticmethod
    def create_all(db: Session, result_id: int, reasons: list[tuple[str, str, float]]) -> None:
        """추천 도메인이 전달한 구조화 이유를 ORM 모델로 생성한다."""
        RecommendationReasonRepository.add_all(
            db,
            [
                RecommendationReason(
                    recommendation_result_id=result_id,
                    reason_type=reason_type,
                    reason_text=reason_text,
                    contribution_score=Decimal(str(score)),
                )
                for reason_type, reason_text, score in reasons
            ],
        )
