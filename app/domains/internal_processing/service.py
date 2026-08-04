"""INT-001~003 내부 처리 서비스."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.internal_processing.schemas import (
    DomainNotificationEvent,
    InternalResult,
    RecommendationUpdateEvent,
)
from app.domains.notifications.service import NotificationService
from app.domains.project_embeddings.service import ProjectEmbeddingService
from app.domains.project_members.service import ProjectMemberService
from app.domains.project_positions.service import ProjectPositionService
from app.domains.projects.service import ProjectService
from app.domains.recommendation_results.service import RecommendationResultService
from app.domains.user_embeddings.service import UserEmbeddingService
from app.domains.users.service import UserService


class InternalProcessingService:
    """추천 갱신, 모집 종료와 도메인 알림 내부 작업을 제공한다."""

    @staticmethod
    def refresh_recommendation_data(
        db: Session, event: RecommendationUpdateEvent
    ) -> InternalResult:
        """프로필·프로젝트 변경에 따른 추천 데이터를 멱등하게 갱신한다."""
        if event.target_type == "USER":
            if UserService.get_by_id(db, event.target_id) is None:
                return InternalResult(success=False, failed_count=1, result="FAILED")
            changed = False
            if get_settings().gemini_api_key:
                changed = UserEmbeddingService.refresh(db, event.target_id)
            deleted = RecommendationResultService.delete_by_user(db, event.target_id)
            db.commit()
            return InternalResult(processed_count=1 if changed or deleted else 0)

        changed = ProjectService.update_recommendation_text(
            db,
            event.target_id,
            embedding_version=event.model_version,
        )
        if get_settings().gemini_api_key:
            changed = ProjectEmbeddingService.refresh(db, event.target_id) or changed
        deleted = RecommendationResultService.delete_by_project(db, event.target_id)
        db.commit()
        return InternalResult(processed_count=1 if changed or deleted else 0)

    @staticmethod
    def close_recruitment(db: Session, *, now: datetime | None = None) -> InternalResult:
        """마감일 경과 또는 모든 포지션 충원 프로젝트의 모집을 종료한다."""
        current = now or datetime.now(timezone.utc)
        processed = 0
        failed = 0
        for project in ProjectService.recruiting_for_automatic_close(db):
            try:
                with db.begin_nested():
                    deadline = project.recruitment_deadline
                    if deadline.tzinfo is None:
                        deadline = deadline.replace(tzinfo=timezone.utc)
                    positions = ProjectPositionService.list_by_project(db, project.project_id)
                    all_filled = bool(positions) and all(
                        ProjectMemberService.active_position_count(
                            db, project.project_id, position.project_position_id
                        )
                        >= position.required_count
                        for position in positions
                    )
                    if deadline > current and not all_filled:
                        continue
                    ProjectService.close_recruitment_automatically(project, current)
                    NotificationService.recruitment_closed(
                        db, project.owner_user_id, project.project_id
                    )
                    processed += 1
            except Exception:
                failed += 1
        db.commit()
        return InternalResult(
            success=failed == 0,
            processed_count=processed,
            failed_count=failed,
            result="SUCCESS" if failed == 0 else "PARTIAL_SUCCESS",
        )

    @staticmethod
    def create_domain_notification(db: Session, event: DomainNotificationEvent) -> InternalResult:
        """확정 이벤트 유형을 사용자 알림으로 변환하고 중복 생성을 방지한다."""
        created = False
        if event.event_type == "APPLICATION_RECEIVED":
            created = NotificationService.application_received(
                db, event.recipient_user_id, event.application_id
            )
        elif event.event_type in {"APPLICATION_ACCEPTED", "APPLICATION_REJECTED"}:
            created = NotificationService.application_decided(
                db,
                event.recipient_user_id,
                event.application_id,
                accepted=event.event_type == "APPLICATION_ACCEPTED",
            )
        elif event.event_type == "RECRUITMENT_CLOSED":
            created = NotificationService.recruitment_closed(
                db, event.recipient_user_id, event.project_id
            )
        else:
            member_event = {
                "MEMBER_LEFT": "LEFT",
                "MEMBER_REMOVED": "REMOVED",
                "MEMBER_RESTORED": "RESTORED",
            }[event.event_type]
            created = NotificationService.team_member_changed(
                db,
                event.recipient_user_id,
                event.project_id,
                event_type=member_event,
            )
        db.commit()
        return InternalResult(processed_count=1 if created else 0)
