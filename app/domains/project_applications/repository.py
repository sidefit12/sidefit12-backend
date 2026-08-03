"""프로젝트 지원 생성, 조회, 상태 변경 데이터 접근 연산."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.project_applications.models import ProjectApplication


class ProjectApplicationRepository:
    @staticmethod
    def find(db: Session, application_id: int, *, lock: bool = False):
        """지원 내역을 조회하고 필요하면 갱신 잠금을 적용한다."""
        query = select(ProjectApplication).where(
            ProjectApplication.project_application_id == application_id
        )
        if lock:
            query = query.with_for_update()
        return db.scalar(query)

    @staticmethod
    def find_by_user(db: Session, project_id: int, user_id: int):
        return db.scalar(
            select(ProjectApplication).where(
                ProjectApplication.project_id == project_id,
                ProjectApplication.applicant_user_id == user_id,
            )
        )

    @staticmethod
    def accepted_counts(db: Session, project_id: int) -> dict[int, int]:
        rows = db.execute(
            select(ProjectApplication.project_position_id, func.count())
            .where(
                ProjectApplication.project_id == project_id,
                ProjectApplication.application_status == "ACCEPTED",
            )
            .group_by(ProjectApplication.project_position_id)
        ).all()
        return dict(rows)

    @staticmethod
    def add(
        db: Session,
        *,
        project_id: int,
        position_id: int,
        applicant_user_id: int,
        message: str,
    ) -> ProjectApplication:
        """새로운 대기 지원을 생성한다."""
        application = ProjectApplication(
            project_id=project_id,
            project_position_id=position_id,
            applicant_user_id=applicant_user_id,
            application_message=message,
            application_status="PENDING",
        )
        db.add(application)
        db.flush()
        return application

    @staticmethod
    def page_by_user(
        db: Session, user_id: int, *, page: int, size: int, status: str | None
    ) -> tuple[list[ProjectApplication], int]:
        """사용자의 지원 목록을 페이지로 조회한다."""
        query = select(ProjectApplication).where(ProjectApplication.applicant_user_id == user_id)
        if status:
            query = query.where(ProjectApplication.application_status == status)
        return ProjectApplicationRepository._page(db, query, page, size)

    @staticmethod
    def page_by_project(
        db: Session,
        project_id: int,
        *,
        page: int,
        size: int,
        status: str | None,
        position_id: int | None,
    ) -> tuple[list[ProjectApplication], int]:
        """프로젝트의 지원 목록을 페이지로 조회한다."""
        query = select(ProjectApplication).where(ProjectApplication.project_id == project_id)
        if status:
            query = query.where(ProjectApplication.application_status == status)
        if position_id:
            query = query.where(ProjectApplication.project_position_id == position_id)
        return ProjectApplicationRepository._page(db, query, page, size)

    @staticmethod
    def status_counts(
        db: Session, *, user_id: int | None = None, project_id: int | None = None
    ) -> dict[str, int]:
        """범위별 지원 상태 집계를 반환한다."""
        query = select(ProjectApplication.application_status, func.count()).group_by(
            ProjectApplication.application_status
        )
        if user_id is not None:
            query = query.where(ProjectApplication.applicant_user_id == user_id)
        if project_id is not None:
            query = query.where(ProjectApplication.project_id == project_id)
        return dict(db.execute(query).all())

    @staticmethod
    def _page(db: Session, query, page: int, size: int):
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            db.scalars(
                query.order_by(
                    ProjectApplication.applied_at.desc(),
                    ProjectApplication.project_application_id.desc(),
                )
                .offset(page * size)
                .limit(size)
            ).all()
        )
        return items, total
