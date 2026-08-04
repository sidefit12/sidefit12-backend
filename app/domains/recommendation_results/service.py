"""추천 결과 서비스."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.recommendation_results.models import RecommendationResult
from app.domains.recommendation_results.repository import RecommendationResultRepository


class RecommendationResultService:
    @staticmethod
    def list_by_user(db: Session, user_id: int, version: str) -> list[RecommendationResult]:
        return RecommendationResultRepository.list_by_user(db, user_id, version)

    @staticmethod
    def create(
        db: Session,
        *,
        user_id: int,
        project_id: int,
        rule_score: float,
        final_score: float,
        version: str,
        generated_at: datetime,
        expires_at: datetime,
    ) -> RecommendationResult:
        """검증된 추천 점수를 ORM 모델로 생성해 저장한다."""
        return RecommendationResultRepository.add(
            db,
            RecommendationResult(
                user_id=user_id,
                project_id=project_id,
                rule_score=Decimal(str(rule_score)),
                semantic_score=None,
                final_score=Decimal(str(final_score)),
                recommendation_version=version,
                generated_at=generated_at,
                expires_at=expires_at,
            ),
        )

    @staticmethod
    def delete_by_user(db: Session, user_id: int) -> None:
        RecommendationResultRepository.delete_by_user(db, user_id)
