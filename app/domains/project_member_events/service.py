"""프로젝트 팀원 이벤트 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_member_events.repository import ProjectMemberEventRepository


class ProjectMemberEventService:
    """다른 도메인에 팀원 이벤트 기록 기능을 제공한다."""

    @staticmethod
    def add_joined(db: Session, project_member_id: int, actor_user_id: int) -> None:
        ProjectMemberEventRepository.add_joined(db, project_member_id, actor_user_id)
