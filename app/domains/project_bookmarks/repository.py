"""프로젝트 북마크 조회 연산."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.project_bookmarks.models import ProjectBookmark


class ProjectBookmarkRepository:
    @staticmethod
    def exists(db: Session, user_id: int, project_id: int) -> bool:
        return (
            db.scalar(
                select(ProjectBookmark.project_bookmark_id).where(
                    ProjectBookmark.user_id == user_id, ProjectBookmark.project_id == project_id
                )
            )
            is not None
        )
