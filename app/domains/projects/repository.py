"""프로젝트와 모집 정보의 데이터 접근 연산."""

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.domains.projects.models import Project, ProjectTechStack, ProjectTopic


class ProjectRepository:
    @staticmethod
    def find(db: Session, project_id: int, *, include_deleted: bool = False) -> Project | None:
        query = select(Project).where(Project.project_id == project_id)
        if not include_deleted:
            query = query.where(Project.deleted_at.is_(None))
        return db.scalar(query)

    @staticmethod
    def list(
        db: Session,
        *,
        page: int,
        size: int,
        owner_user_id: int | None = None,
        recruitment_status: str | None = None,
        work_type: str | None = None,
        topic_id: int | None = None,
        tech_stack_id: int | None = None,
        project_ids: set[int] | None = None,
        keyword: str | None = None,
    ) -> tuple[list[Project], int]:
        query = select(Project).where(Project.deleted_at.is_(None), Project.visibility == "PUBLIC")
        if owner_user_id is not None:
            query = query.where(Project.owner_user_id == owner_user_id)
        if recruitment_status:
            query = query.where(Project.recruitment_status == recruitment_status)
        if work_type:
            query = query.where(Project.work_type == work_type)
        if topic_id:
            query = query.join(ProjectTopic).where(ProjectTopic.topic_id == topic_id)
        if tech_stack_id:
            query = query.join(ProjectTechStack).where(
                ProjectTechStack.tech_stack_id == tech_stack_id
            )
        if project_ids is not None:
            query = query.where(Project.project_id.in_(project_ids))
        if keyword:
            pattern = f"%{keyword.strip()}%"
            query = query.where(or_(Project.title.ilike(pattern), Project.summary.ilike(pattern)))
        query = query.distinct()
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            db.scalars(
                query.order_by(Project.created_at.desc()).offset((page - 1) * size).limit(size)
            ).all()
        )
        return items, total

    @staticmethod
    def replace_topics(db: Session, project_id: int, items) -> None:
        db.execute(delete(ProjectTopic).where(ProjectTopic.project_id == project_id))
        db.add_all(
            [
                ProjectTopic(
                    project_id=project_id, topic_id=item.topic_id, is_primary=item.is_primary
                )
                for item in items
            ]
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
