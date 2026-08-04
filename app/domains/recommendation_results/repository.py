"""추천 결과 repository."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.recommendation_results.models import RecommendationResult


class RecommendationResultRepository:
    @staticmethod
    def list_by_user(db: Session, user_id: int, version: str) -> list[RecommendationResult]:
        return list(
            db.scalars(
                select(RecommendationResult)
                .where(
                    RecommendationResult.user_id == user_id,
                    RecommendationResult.recommendation_version == version,
                )
                .order_by(
                    RecommendationResult.final_score.desc(), RecommendationResult.project_id.desc()
                )
            ).all()
        )

    @staticmethod
    def add(db: Session, result: RecommendationResult) -> RecommendationResult:
        db.add(result)
        db.flush()
        return result

    @staticmethod
    def delete_by_user(db: Session, user_id: int) -> None:
        db.execute(delete(RecommendationResult).where(RecommendationResult.user_id == user_id))
