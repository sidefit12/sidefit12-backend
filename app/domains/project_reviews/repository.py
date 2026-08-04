"""프로젝트 리뷰 데이터 접근 계층."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.project_reviews.models import ProjectReview


class ProjectReviewRepository:
    @staticmethod
    def find(db: Session, review_id: int):
        return db.scalar(select(ProjectReview).where(ProjectReview.project_review_id == review_id))

    @staticmethod
    def find_by_reviewer(db: Session, project_id: int, user_id: int):
        return db.scalar(
            select(ProjectReview).where(
                ProjectReview.project_id == project_id, ProjectReview.reviewer_user_id == user_id
            )
        )

    @staticmethod
    def page(db: Session, project_id: int, *, page: int, size: int, sort: str):
        query = select(ProjectReview).where(ProjectReview.project_id == project_id)
        order = {
            "LATEST": ProjectReview.created_at.desc(),
            "RATING_HIGH": ProjectReview.rating.desc(),
            "RATING_LOW": ProjectReview.rating.asc(),
        }[sort]
        total = (
            db.scalar(
                select(func.count())
                .select_from(ProjectReview)
                .where(ProjectReview.project_id == project_id)
            )
            or 0
        )
        return list(
            db.scalars(
                query.order_by(order, ProjectReview.project_review_id.desc())
                .offset(page * size)
                .limit(size)
            ).all()
        ), total

    @staticmethod
    def average(db: Session, project_id: int):
        return float(
            db.scalar(
                select(func.avg(ProjectReview.rating)).where(ProjectReview.project_id == project_id)
            )
            or 0
        )

    @staticmethod
    def add(db: Session, project_id: int, user_id: int, request):
        review = ProjectReview(
            project_id=project_id,
            reviewer_user_id=user_id,
            rating=request.rating,
            content=request.content.strip() if request.content else None,
        )
        db.add(review)
        db.flush()
        return review

    @staticmethod
    def delete(db: Session, review):
        db.delete(review)
