"""프로젝트 모집 포지션 데이터 접근 연산."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.project_positions.models import ProjectPosition


class ProjectPositionRepository:
    """모집 포지션의 저장과 조회를 담당한다."""

    @staticmethod
    def replace(db: Session, project_id: int, items) -> None:
        """프로젝트의 모집 포지션을 요청 목록으로 교체한다."""
        db.execute(delete(ProjectPosition).where(ProjectPosition.project_id == project_id))
        db.add_all(
            [
                ProjectPosition(
                    project_id=project_id,
                    role_id=item.role_id,
                    position_title=item.position_title.strip(),
                    responsibilities=item.responsibilities,
                    required_count=item.required_count,
                    required_level=item.required_level,
                )
                for item in items
            ]
        )

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
