"""프로젝트 모집 포지션 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_positions.repository import ProjectPositionRepository


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
        """프로젝트 모집 포지션을 전체 교체한다."""
        ProjectPositionRepository.replace(db, project_id, items)

    @staticmethod
    def list_by_project(db: Session, project_id: int):
        """프로젝트의 모집 포지션을 조회한다."""
        return ProjectPositionRepository.list_by_project(db, project_id)

    @staticmethod
    def find_project_ids_by_role(db: Session, role_id: int) -> set[int]:
        """지정한 역할을 모집하는 프로젝트 식별자를 조회한다."""
        return ProjectPositionRepository.find_project_ids_by_role(db, role_id)
