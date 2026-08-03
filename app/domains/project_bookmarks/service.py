"""프로젝트 북마크 등록, 해제 및 목록 조회 비즈니스 로직."""

import math

from sqlalchemy.orm import Session

from app.domains.project_bookmarks.repository import ProjectBookmarkRepository
from app.domains.projects.exceptions import ProjectNotFoundError
from app.domains.projects.schemas import PageMeta, ProjectPageData
from app.domains.users.models import User


class ProjectBookmarkService:
    """BOOKMARK-001~003의 북마크 규칙을 제공한다."""

    @staticmethod
    def exists(db: Session, user_id: int, project_id: int) -> bool:
        return ProjectBookmarkRepository.exists(db, user_id, project_id)

    @staticmethod
    def add(db: Session, user: User, project_id: int) -> dict[str, object]:
        """공개 가능한 프로젝트를 멱등하게 북마크한다."""
        from app.domains.projects.service import ProjectService

        project = ProjectService.find_visible(db, project_id, user)
        if project is None:
            raise ProjectNotFoundError(project_id)
        if not ProjectBookmarkRepository.exists(db, user.user_id, project_id):
            ProjectBookmarkRepository.add(db, user.user_id, project_id)
            db.commit()
        return {"project_id": project_id, "bookmarked": True}

    @staticmethod
    def remove(db: Session, user: User, project_id: int) -> dict[str, object]:
        """공개 가능한 프로젝트의 북마크를 멱등하게 해제한다."""
        from app.domains.projects.service import ProjectService

        project = ProjectService.find_visible(db, project_id, user)
        if project is None:
            raise ProjectNotFoundError(project_id)
        ProjectBookmarkRepository.delete(db, user.user_id, project_id)
        db.commit()
        return {"project_id": project_id, "bookmarked": False}

    @staticmethod
    def page(
        db: Session,
        user: User,
        *,
        page: int,
        size: int,
        include_closed: bool,
    ) -> tuple[ProjectPageData, PageMeta]:
        """삭제·숨김·비공개 프로젝트를 제외한 북마크 목록을 최신순으로 반환한다."""
        from app.domains.projects.service import ProjectService

        projects = []
        for bookmark in ProjectBookmarkRepository.list_by_user(db, user.user_id):
            project = ProjectService.find_visible(db, bookmark.project_id, user)
            if project is None:
                continue
            if not include_closed and project.recruitment_status == "CLOSED":
                continue
            projects.append(project)
        total = len(projects)
        selected = projects[page * size : (page + 1) * size]
        return ProjectPageData(
            items=[ProjectService.card(db, project, user) for project in selected]
        ), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )
