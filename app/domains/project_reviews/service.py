"""프로젝트 리뷰 비즈니스 규칙."""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.project_members.service import ProjectMemberService
from app.domains.project_reviews.exceptions import (
    ReviewAccessDeniedError,
    ReviewAlreadyExistsError,
    ReviewInvalidStateError,
    ReviewNotFoundError,
    ReviewOwnershipRequiredError,
)
from app.domains.project_reviews.repository import ProjectReviewRepository
from app.domains.project_reviews.schemas import ReviewerSummary, ReviewPageData, ReviewResource
from app.domains.projects.schemas import PageMeta
from app.domains.projects.service import ProjectService
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User
from app.domains.users.service import UserService


class ProjectReviewService:
    @staticmethod
    def page(db: Session, project_id: int, viewer: User | None, *, page: int, size: int, sort: str):
        ProjectService.find_or_raise_visible(db, project_id, viewer)
        items, total = ProjectReviewRepository.page(db, project_id, page=page, size=size, sort=sort)
        return ReviewPageData(
            average_rating=round(ProjectReviewRepository.average(db, project_id), 2),
            review_count=total,
            items=[ProjectReviewService._resource(db, item, viewer) for item in items],
        ), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )

    @staticmethod
    def create(db: Session, user: User, project_id: int, request):
        project = ProjectService.get_for_application(db, project_id)
        if project.project_status != "COMPLETED":
            raise ReviewInvalidStateError()
        if not ProjectMemberService.is_active_or_former_member(db, project_id, user.user_id):
            raise ReviewAccessDeniedError()
        if ProjectReviewRepository.find_by_reviewer(db, project_id, user.user_id):
            raise ReviewAlreadyExistsError()
        review = ProjectReviewRepository.add(db, project_id, user.user_id, request)
        db.commit()
        return ProjectReviewService._resource(db, review, user)

    @staticmethod
    def update(db: Session, user: User, review_id: int, request):
        review = ProjectReviewRepository.find(db, review_id)
        if review is None:
            raise ReviewNotFoundError()
        if review.reviewer_user_id != user.user_id:
            raise ReviewOwnershipRequiredError()
        for field in request.model_fields_set:
            setattr(
                review,
                field,
                getattr(request, field).strip()
                if field == "content" and getattr(request, field)
                else getattr(request, field),
            )
        review.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ProjectReviewService._resource(db, review, user)

    @staticmethod
    def delete(db: Session, user: User, review_id: int):
        review = ProjectReviewRepository.find(db, review_id)
        if review is None:
            raise ReviewNotFoundError()
        if review.reviewer_user_id != user.user_id:
            raise ReviewOwnershipRequiredError()
        ProjectReviewRepository.delete(db, review)
        db.commit()

    @staticmethod
    def _resource(db, review, viewer):
        user = UserService.get_by_id(db, review.reviewer_user_id)
        profile = ProfileService.get_user_summary(db, user.user_id)
        return ReviewResource(
            review_id=review.project_review_id,
            project_id=review.project_id,
            rating=review.rating,
            content=review.content,
            created_at=review.created_at,
            reviewer=ReviewerSummary(
                user_id=user.user_id,
                nickname=user.nickname,
                user_status=user.user_status,
                system_role=user.system_role,
                onboarding_completed=bool(profile["onboarding_completed"]),
                profile_image_url=profile["profile_image_url"],
                email=user.email if viewer and viewer.user_id == user.user_id else None,
            ),
        )
