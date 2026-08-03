"""프로젝트 북마크 조회 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_bookmarks.repository import ProjectBookmarkRepository


class ProjectBookmarkService:
    @staticmethod
    def exists(db: Session, user_id: int, project_id: int) -> bool:
        return ProjectBookmarkRepository.exists(db, user_id, project_id)
