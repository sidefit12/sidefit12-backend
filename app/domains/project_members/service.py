"""프로젝트 팀원 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_member_events.service import ProjectMemberEventService
from app.domains.project_members.repository import ProjectMemberRepository


class ProjectMemberService:
    """프로젝트 생성과 삭제에 필요한 팀원 규칙을 제공한다."""

    @staticmethod
    def add_owner(db: Session, project_id: int, user_id: int, position_id: int) -> None:
        member = ProjectMemberRepository.add_owner(db, project_id, user_id, position_id)
        ProjectMemberEventService.add_joined(db, member.project_member_id, user_id)

    @staticmethod
    def add_accepted_member(
        db: Session,
        *,
        project_id: int,
        user_id: int,
        position_id: int,
        application_id: int,
        actor_user_id: int,
    ):
        """승인된 지원자를 추가하고 합류 이벤트를 기록한다."""
        member = ProjectMemberRepository.add_member(
            db,
            project_id=project_id,
            user_id=user_id,
            position_id=position_id,
            application_id=application_id,
        )
        ProjectMemberEventService.add_joined(db, member.project_member_id, actor_user_id)
        return member

    @staticmethod
    def active_count(db: Session, project_id: int) -> int:
        return ProjectMemberRepository.active_member_count(db, project_id)

    @staticmethod
    def has_confirmed_members(db: Session, project_id: int) -> bool:
        return ProjectMemberRepository.active_member_count(db, project_id, exclude_owner=True) > 0
