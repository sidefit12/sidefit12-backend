"""프로젝트 지원 조회 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_applications.repository import ProjectApplicationRepository


class ProjectApplicationService:
    @staticmethod
    def find_by_user(db: Session, project_id: int, user_id: int):
        return ProjectApplicationRepository.find_by_user(db, project_id, user_id)

    @staticmethod
    def accepted_counts(db: Session, project_id: int) -> dict[int, int]:
        return ProjectApplicationRepository.accepted_counts(db, project_id)
