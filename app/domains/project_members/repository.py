"""프로젝트 팀원 데이터 접근 연산."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.project_members.models import ProjectMember


class ProjectMemberRepository:
    """프로젝트 팀원의 생성과 집계를 담당한다."""

    @staticmethod
    def add_owner(db: Session, project_id: int, user_id: int, position_id: int) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            project_position_id=position_id,
            member_type="OWNER",
        )
        db.add(member)
        db.flush()
        return member

    @staticmethod
    def active_member_count(db: Session, project_id: int, *, exclude_owner: bool = False) -> int:
        query = (
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project_id, ProjectMember.member_status == "ACTIVE")
        )
        if exclude_owner:
            query = query.where(ProjectMember.member_type != "OWNER")
        return db.scalar(query) or 0
