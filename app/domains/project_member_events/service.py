"""프로젝트 팀원 이벤트 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_member_events.repository import ProjectMemberEventRepository


class ProjectMemberEventService:
    """다른 도메인에 팀원 이벤트 기록 기능을 제공한다."""

    @staticmethod
    def add_joined(db: Session, project_member_id: int, actor_user_id: int) -> None:
        ProjectMemberEventRepository.add_joined(db, project_member_id, actor_user_id)

    @staticmethod
    def add_status_event(
        db: Session,
        *,
        project_member_id: int,
        event_type: str,
        actor_user_id: int | None,
        reason: str | None,
    ) -> None:
        """팀원 상태 변경 이력을 기록한다."""
        ProjectMemberEventRepository.add(
            db,
            project_member_id=project_member_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            reason=reason,
        )

    @staticmethod
    def page_by_member_ids(db: Session, member_ids: set[int], *, page: int, size: int):
        """지정된 팀원들의 이벤트 페이지를 반환한다."""
        return ProjectMemberEventRepository.page_by_member_ids(db, member_ids, page=page, size=size)
