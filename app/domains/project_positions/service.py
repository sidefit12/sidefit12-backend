"""프로젝트 모집 포지션 서비스."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.project_members.models import ProjectMember
from app.domains.project_positions.repository import ProjectPositionRepository
from app.domains.projects.exceptions import (
    CannotRemoveReferencedPositionError,
    ReferenceNotFoundError,
)


class ProjectPositionService:
    """Projects 도메인에 모집 포지션 연산을 제공한다."""

    @staticmethod
    def find(db: Session, position_id: int, *, lock: bool = False):
        """식별자로 모집 포지션을 조회한다."""
        return ProjectPositionRepository.find(db, position_id, lock=lock)

    @staticmethod
    def close(db: Session, position) -> None:
        """모집 정원이 찬 포지션을 마감한다."""
        position.position_status = "CLOSED"

    @staticmethod
    def open(db: Session, position) -> None:
        """팀원 이탈로 자리가 생긴 포지션을 다시 연다."""
        position.position_status = "OPEN"

    @staticmethod
    def replace(db: Session, project_id: int, items) -> None:
        """기존 포지션은 수정하고 새 포지션만 추가하며 안전한 항목만 제거한다."""
        existing = list(ProjectPositionRepository.list_by_project(db, project_id))
        existing_ids = {position.project_position_id for position in existing}
        requested_ids = [
            item.project_position_id for item in items if item.project_position_id is not None
        ]
        invalid_ids = sorted(set(requested_ids) - existing_ids)
        if invalid_ids:
            raise ReferenceNotFoundError("position", invalid_ids)

        removed_ids = existing_ids - set(requested_ids)
        if removed_ids:
            referenced_ids = set(
                db.scalars(
                    select(ProjectMember.project_position_id).where(
                        ProjectMember.project_id == project_id,
                        ProjectMember.project_position_id.in_(removed_ids),
                    )
                ).all()
            )
            if referenced_ids:
                raise CannotRemoveReferencedPositionError(sorted(referenced_ids))

        ProjectPositionRepository.sync(db, project_id, items, existing)

    @staticmethod
    def list_by_project(db: Session, project_id: int):
        """프로젝트의 모집 포지션을 조회한다."""
        return ProjectPositionRepository.list_by_project(db, project_id)

    @staticmethod
    def find_project_ids_by_role(db: Session, role_id: int) -> set[int]:
        """지정한 역할을 모집하는 프로젝트 식별자를 조회한다."""
        return ProjectPositionRepository.find_project_ids_by_role(db, role_id)
