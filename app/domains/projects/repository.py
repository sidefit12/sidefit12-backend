"""프로젝트와 모집 정보의 데이터 접근 연산."""

from datetime import datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.domains.projects.models import Project, ProjectTechStack, ProjectTopic


class ProjectRepository:
    @staticmethod
    def list_embedding_target_ids(db: Session, *, after_project_id: int, limit: int) -> list[int]:
        """임베딩 백필 대상 프로젝트 식별자를 커서 방식으로 조회한다."""
        return list(
            db.scalars(
                select(Project.project_id)
                .where(
                    Project.deleted_at.is_(None),
                    Project.moderation_status == "VISIBLE",
                    Project.project_id > after_project_id,
                )
                .order_by(Project.project_id)
                .limit(limit)
            ).all()
        )

    @staticmethod
    def find(db: Session, project_id: int, *, include_deleted: bool = False) -> Project | None:
        query = select(Project).where(Project.project_id == project_id)
        if not include_deleted:
            query = query.where(Project.deleted_at.is_(None))
        return db.scalar(query)

    @staticmethod
    def titles_by_ids(db: Session, project_ids: set[int]) -> dict[int, str]:
        """프로젝트 식별자별 제목을 한 번의 쿼리로 조회한다."""
        if not project_ids:
            return {}
        return dict(
            db.execute(
                select(Project.project_id, Project.title).where(Project.project_id.in_(project_ids))
            ).all()
        )

    @staticmethod
    def has_active_owned_project(db: Session, user_id: int) -> bool:
        """사용자가 책임지고 있는 종료 전 프로젝트가 있는지 확인한다."""
        return (
            db.scalar(
                select(Project.project_id).where(
                    Project.owner_user_id == user_id,
                    Project.deleted_at.is_(None),
                    Project.project_status.not_in(("COMPLETED", "CANCELED")),
                )
            )
            is not None
        )

    @staticmethod
    def count_by_owner(db: Session, user_id: int) -> int:
        """사용자가 작성한 삭제되지 않은 프로젝트 수를 반환한다."""
        return (
            db.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.owner_user_id == user_id, Project.deleted_at.is_(None))
            )
            or 0
        )

    @staticmethod
    def recruiting_candidates(db: Session) -> list[Project]:
        """추천 가능한 공개 모집 프로젝트를 최신순으로 반환한다."""
        return list(
            db.scalars(
                select(Project)
                .where(
                    Project.deleted_at.is_(None),
                    Project.moderation_status == "VISIBLE",
                    Project.visibility == "PUBLIC",
                    Project.recruitment_status == "RECRUITING",
                )
                .order_by(Project.created_at.desc(), Project.project_id.desc())
            ).all()
        )

    @staticmethod
    def search(
        db: Session,
        *,
        page: int,
        size: int,
        owner_user_id: int | None = None,
        include_deleted: bool = False,
        project_status: str | None = None,
        recruitment_status: str | None = None,
        work_type: str | None = None,
        topic_ids: list[int] | None = None,
        tech_stack_ids: list[int] | None = None,
        project_ids: set[int] | None = None,
        keyword: str | None = None,
        sort: str = "LATEST",
    ) -> tuple[list[Project], int]:
        query = select(Project).where(Project.moderation_status == "VISIBLE")
        if not include_deleted:
            query = query.where(Project.deleted_at.is_(None))
        if owner_user_id is None:
            query = query.where(Project.visibility == "PUBLIC")
        if owner_user_id is not None:
            query = query.where(Project.owner_user_id == owner_user_id)
        if project_status:
            query = query.where(Project.project_status == project_status)
        if recruitment_status:
            query = query.where(Project.recruitment_status == recruitment_status)
        if work_type:
            query = query.where(Project.work_type == work_type)
        if topic_ids:
            query = query.join(ProjectTopic).where(ProjectTopic.topic_id.in_(topic_ids))
        if tech_stack_ids:
            query = query.join(ProjectTechStack).where(
                ProjectTechStack.tech_stack_id.in_(tech_stack_ids)
            )
        if project_ids is not None:
            query = query.where(Project.project_id.in_(project_ids))
        if keyword:
            pattern = f"%{keyword.strip()}%"
            query = query.where(or_(Project.title.ilike(pattern), Project.summary.ilike(pattern)))
        query = query.distinct()
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        ordering = (
            (Project.recruitment_deadline.asc(), Project.project_id.desc())
            if sort == "DEADLINE"
            else (Project.created_at.desc(), Project.project_id.desc())
        )
        items = list(db.scalars(query.order_by(*ordering).offset(page * size).limit(size)).all())
        return items, total

    @staticmethod
    def replace_topics(db: Session, project_id: int, topic_ids: list[int]) -> None:
        db.execute(delete(ProjectTopic).where(ProjectTopic.project_id == project_id))
        db.add_all(
            [ProjectTopic(project_id=project_id, topic_id=topic_id) for topic_id in topic_ids]
        )

    @staticmethod
    def replace_tech_stacks(db: Session, project_id: int, items) -> None:
        db.execute(delete(ProjectTechStack).where(ProjectTechStack.project_id == project_id))
        db.add_all(
            [
                ProjectTechStack(
                    project_id=project_id,
                    tech_stack_id=item.tech_stack_id,
                    requirement_type=item.requirement_type,
                    required_level=item.required_level,
                )
                for item in items
            ]
        )

    @staticmethod
    def topics(db: Session, project_id: int):
        return db.scalars(
            select(ProjectTopic)
            .where(ProjectTopic.project_id == project_id)
            .order_by(ProjectTopic.is_primary.desc(), ProjectTopic.project_topic_id)
        ).all()

    @staticmethod
    def tech_stacks(db: Session, project_id: int):
        return db.scalars(
            select(ProjectTechStack)
            .where(ProjectTechStack.project_id == project_id)
            .order_by(ProjectTechStack.project_tech_stack_id)
        ).all()

    @staticmethod
    def hide(project: Project) -> None:
        """관리자 조치로 프로젝트를 숨김 상태로 변경한다."""
        project.moderation_status = "HIDDEN"

    @staticmethod
    def recruiting_for_automatic_close(db: Session) -> list[Project]:
        """자동 모집 종료 검사의 대상 프로젝트를 잠금 조회한다."""
        return list(
            db.scalars(
                select(Project)
                .where(
                    Project.recruitment_status == "RECRUITING",
                    Project.deleted_at.is_(None),
                )
                .with_for_update(skip_locked=True)
            ).all()
        )

    @staticmethod
    def update_recommendation_text(
        project: Project, *, normalized_text: str, embedding_version: str
    ) -> bool:
        """추천용 정규화 텍스트와 처리 버전을 변경한다."""
        if (
            project.normalized_text == normalized_text
            and project.embedding_version == embedding_version
        ):
            return False
        project.normalized_text = normalized_text
        project.embedding_version = embedding_version
        return True

    @staticmethod
    def close_recruitment(project: Project, closed_at: datetime) -> None:
        """프로젝트 모집을 종료 상태로 변경한다."""
        project.recruitment_status = "CLOSED"
        project.closed_at = closed_at
        project.updated_at = closed_at
