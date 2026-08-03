"""프로젝트 팀원 이벤트 데이터 접근 연산."""

from sqlalchemy.orm import Session

from app.domains.project_member_events.models import ProjectMemberEvent


class ProjectMemberEventRepository:
    """프로젝트 팀원 이벤트 생성을 담당한다."""

    @staticmethod
    def add_joined(db: Session, project_member_id: int, actor_user_id: int) -> None:
        db.add(
            ProjectMemberEvent(
                project_member_id=project_member_id,
                event_type="JOINED",
                actor_user_id=actor_user_id,
            )
        )
