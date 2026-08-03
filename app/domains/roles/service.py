"""역할 목록 제공과 선택값 검증 service."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.domains.roles.models import Role
from app.domains.roles.repository import RoleRepository
from app.domains.users.exceptions import InvalidProfileSelectionError


class RoleService:
    """활성 역할 조회와 프로필 역할 선택 검증을 담당한다."""

    @staticmethod
    def list(
        db: Session, *, include_inactive: bool = False, keyword: str | None = None
    ) -> Sequence[Role]:
        """조회 조건에 맞는 역할 기준정보를 반환한다."""
        return RoleRepository.list(db, active_only=not include_inactive, keyword=keyword)

    @staticmethod
    def list_active(db: Session) -> Sequence[Role]:
        """신규 선택에 사용할 활성 역할 목록을 반환한다."""
        return RoleService.list(db)

    @staticmethod
    def find_by_ids(db: Session, ids: set[int]) -> Sequence[Role]:
        """식별자에 해당하는 역할을 활성 상태와 관계없이 조회한다."""
        return RoleRepository.find_by_ids(db, ids)

    @staticmethod
    def validate_active_ids(db: Session, ids: set[int]) -> Sequence[Role]:
        """선택한 모든 역할이 존재하고 활성 상태인지 확인한다."""
        items = RoleRepository.find_by_ids(db, ids)
        found_ids = {item.role_id for item in items}
        invalid_ids = sorted(
            ids - found_ids | {item.role_id for item in items if not item.is_active}
        )
        if invalid_ids:
            raise InvalidProfileSelectionError("role", invalid_ids)
        return items
