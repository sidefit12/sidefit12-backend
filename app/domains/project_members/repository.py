"""프로젝트 팀원 데이터 접근 연산."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.project_members.models import ProjectMember


class ProjectMemberRepository:
    """프로젝트 팀원의 생성과 집계를 담당한다."""

    @staticmethod
    def find(db: Session, member_id: int, *, lock: bool = False) -> ProjectMember | None:
        """팀원 식별자로 조회하고 필요하면 갱신 잠금을 적용한다."""
        query = select(ProjectMember).where(ProjectMember.project_member_id == member_id)
        if lock:
            query = query.with_for_update()
        return db.scalar(query)

    @staticmethod
    def find_by_user(
        db: Session, project_id: int, user_id: int, *, lock: bool = False
    ) -> ProjectMember | None:
        """프로젝트와 사용자 식별자로 팀원을 조회한다."""
        query = select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        if lock:
            query = query.with_for_update()
        return db.scalar(query)

    @staticmethod
    def list_by_project(
        db: Session, project_id: int, *, status: str | None = None
    ) -> list[ProjectMember]:
        """프로젝트 팀원을 유형과 합류 순서로 조회한다."""
        query = select(ProjectMember).where(ProjectMember.project_id == project_id)
        if status:
            query = query.where(ProjectMember.member_status == status)
        return list(
            db.scalars(
                query.order_by(
                    ProjectMember.member_type.asc(), ProjectMember.project_member_id.asc()
                )
            ).all()
        )

    @staticmethod
    def add_owner(db: Session, project_id: int, user_id: int) -> ProjectMember:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            project_position_id=None,
            member_type="OWNER",
        )
        db.add(member)
        db.flush()
        return member

    @staticmethod
    def add_member(
        db: Session,
        *,
        project_id: int,
        user_id: int,
        position_id: int,
        application_id: int,
    ) -> ProjectMember:
        """승인된 지원자를 활성 팀원으로 추가한다."""
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            project_position_id=position_id,
            project_application_id=application_id,
            member_type="MEMBER",
            member_status="ACTIVE",
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

    @staticmethod
    def active_position_count(db: Session, project_id: int, position_id: int) -> int:
        """포지션에 배정된 활성 일반 팀원 수를 반환한다."""
        return (
            db.scalar(
                select(func.count())
                .select_from(ProjectMember)
                .where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.project_position_id == position_id,
                    ProjectMember.member_status == "ACTIVE",
                    ProjectMember.member_type == "MEMBER",
                )
            )
            or 0
        )
