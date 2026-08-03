"""프로젝트 지원 조회 연산."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.project_applications.models import ProjectApplication


class ProjectApplicationRepository:
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
