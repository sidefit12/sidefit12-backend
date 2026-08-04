"""홈 화면 영역 조합 서비스."""

from sqlalchemy.orm import Session

from app.domains.home.schemas import ActivitySummary, HomeData, PartialError, ProfileSummary
from app.domains.project_applications.service import ProjectApplicationService
from app.domains.project_bookmarks.service import ProjectBookmarkService
from app.domains.projects.service import ProjectService
from app.domains.recommendations.service import RecommendationService
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User


class HomeService:
    """HOME-001의 프로필·활동·프로젝트 영역을 조합한다."""

    @staticmethod
    def get(db: Session, user: User, section_size: int) -> HomeData:
        profile = ProfileService.recommendation_profile(db, user.user_id)
        counts = ProjectApplicationService.status_counts_by_user(db, user.user_id)
        partial_errors = []
        try:
            recommendations = RecommendationService.top(db, user, section_size)
        except Exception:
            db.rollback()
            recommendations = []
            partial_errors.append(
                PartialError(
                    section="recommendations",
                    code="RECOMMENDATION_UNAVAILABLE",
                    message="추천 영역을 일시적으로 불러올 수 없습니다.",
                )
            )
        latest, _ = ProjectService.page(
            db,
            viewer=user,
            page=0,
            size=section_size,
            owner_user_id=None,
            include_deleted=False,
            project_status=None,
            recruitment_status="RECRUITING",
            work_type=None,
            topic_ids=None,
            tech_stack_ids=None,
            keyword=None,
            sort="LATEST",
        )
        closing, _ = ProjectService.page(
            db,
            viewer=user,
            page=0,
            size=section_size,
            owner_user_id=None,
            include_deleted=False,
            project_status=None,
            recruitment_status="RECRUITING",
            work_type=None,
            topic_ids=None,
            tech_stack_ids=None,
            keyword=None,
            sort="DEADLINE",
        )
        return HomeData(
            profile_summary=ProfileSummary(
                user_id=user.user_id,
                nickname=user.nickname,
                onboarding_completed=profile["onboarding_completed"],
                preferred_work_type=profile["preferred_work_type"],
            ),
            activity_summary=ActivitySummary(
                authored_project_count=ProjectService.count_owned(db, user.user_id),
                application_count=sum(counts.values()),
                pending_application_count=counts.get("PENDING", 0),
                accepted_application_count=counts.get("ACCEPTED", 0),
                bookmarked_project_count=ProjectBookmarkService.count_by_user(db, user.user_id),
            ),
            recommendations=recommendations,
            latest_projects=latest.items,
            closing_soon_projects=closing.items,
            partial_errors=partial_errors,
        )
