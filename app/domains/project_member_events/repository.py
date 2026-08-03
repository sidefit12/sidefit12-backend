"""프로젝트 팀원 이벤트 생성과 조회 데이터 접근 연산."""

from sqlalchemy import func, select
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

    @staticmethod
    def add(
        db: Session,
        *,
        project_member_id: int,
        event_type: str,
        actor_user_id: int | None,
        reason: str | None,
    ) -> None:
        """팀원 상태 변경 이벤트를 생성한다."""
        db.add(
            ProjectMemberEvent(
                project_member_id=project_member_id,
                event_type=event_type,
                actor_user_id=actor_user_id,
                reason=reason,
            )
        )

    @staticmethod
    def page_by_member_ids(db: Session, member_ids: set[int], *, page: int, size: int):
        """지정된 팀원들의 이벤트를 최신순 페이지로 조회한다."""
        query = select(ProjectMemberEvent).where(
            ProjectMemberEvent.project_member_id.in_(member_ids)
        )
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            db.scalars(
                query.order_by(
                    ProjectMemberEvent.created_at.desc(),
                    ProjectMemberEvent.project_member_event_id.desc(),
                )
                .offset(page * size)
                .limit(size)
            ).all()
        )
        return items, total
