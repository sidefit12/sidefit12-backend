"""프로젝트 북마크 생성, 삭제 및 조회 데이터 접근 연산."""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domains.project_bookmarks.models import ProjectBookmark


class ProjectBookmarkRepository:
    @staticmethod
    def add(db: Session, user_id: int, project_id: int) -> ProjectBookmark:
        """사용자와 프로젝트의 북마크 관계를 생성한다."""
        bookmark = ProjectBookmark(user_id=user_id, project_id=project_id)
        db.add(bookmark)
        db.flush()
        return bookmark

    @staticmethod
    def delete(db: Session, user_id: int, project_id: int) -> None:
        """존재하는 북마크 관계를 삭제한다."""
        db.execute(
            delete(ProjectBookmark).where(
                ProjectBookmark.user_id == user_id,
                ProjectBookmark.project_id == project_id,
            )
        )

    @staticmethod
    def list_by_user(db: Session, user_id: int) -> list[ProjectBookmark]:
        """사용자의 북마크를 최신 저장순으로 조회한다."""
        return list(
            db.scalars(
                select(ProjectBookmark)
                .where(ProjectBookmark.user_id == user_id)
                .order_by(
                    ProjectBookmark.created_at.desc(),
                    ProjectBookmark.project_bookmark_id.desc(),
                )
            ).all()
        )

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

    @staticmethod
    def count_by_user(db: Session, user_id: int) -> int:
        """사용자의 북마크 개수를 반환한다."""
        return (
            db.scalar(
                select(func.count())
                .select_from(ProjectBookmark)
                .where(ProjectBookmark.user_id == user_id)
            )
            or 0
        )
