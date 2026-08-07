"""프로젝트 모집 포지션 데이터 접근 연산."""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.project_positions.models import ProjectPosition


class ProjectPositionRepository:
    """모집 포지션의 저장과 조회를 담당한다."""

    @staticmethod
    def find(db: Session, position_id: int, *, lock: bool = False) -> ProjectPosition | None:
        """모집 포지션을 조회하고 필요하면 갱신 잠금을 적용한다."""
        query = select(ProjectPosition).where(ProjectPosition.project_position_id == position_id)
        if lock:
            query = query.with_for_update()
        return db.scalar(query)

    @staticmethod
    def sync(db: Session, project_id: int, items, existing: list[ProjectPosition]) -> None:
        """기존 식별자를 유지하며 모집 포지션 목록을 동기화한다."""
        existing_by_id = {position.project_position_id: position for position in existing}
        requested_ids = {
            item.project_position_id for item in items if item.project_position_id is not None
        }
        removed_ids = set(existing_by_id) - requested_ids
        if removed_ids:
            db.execute(
                delete(ProjectPosition).where(
                    ProjectPosition.project_id == project_id,
                    ProjectPosition.project_position_id.in_(removed_ids),
                )
            )

        now = datetime.now(timezone.utc)
        new_positions = []
        for item in items:
            if item.project_position_id is None:
                new_positions.append(
                    ProjectPosition(
                        project_id=project_id,
                        role_id=item.role_id,
                        position_title=item.position_title.strip(),
                        responsibilities=item.responsibilities,
                        required_count=item.required_count,
                        required_level=item.required_level,
                    )
                )
                continue

            position = existing_by_id[item.project_position_id]
            position.role_id = item.role_id
            position.position_title = item.position_title.strip()
            position.responsibilities = item.responsibilities
            position.required_count = item.required_count
            position.required_level = item.required_level
            position.updated_at = now

        db.add_all(new_positions)

    @staticmethod
    def list_by_project(db: Session, project_id: int):
        """프로젝트에 등록된 모집 포지션을 순서대로 조회한다."""
        return db.scalars(
            select(ProjectPosition)
            .where(ProjectPosition.project_id == project_id)
            .order_by(ProjectPosition.project_position_id)
        ).all()

    @staticmethod
    def find_project_ids_by_role(db: Session, role_id: int) -> set[int]:
        """지정한 역할을 모집하는 프로젝트 식별자를 조회한다."""
        return set(
            db.scalars(
                select(ProjectPosition.project_id).where(ProjectPosition.role_id == role_id)
            ).all()
        )
