"""기술 스택 목록 제공과 선택값 검증 service."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.domains.tech_stacks.models import TechStack
from app.domains.tech_stacks.repository import TechStackRepository
from app.domains.users.exceptions import InvalidProfileSelectionError


class TechStackService:
    """활성 기술 스택 조회와 프로필 선택 검증을 담당한다."""

    @staticmethod
    def list_active(db: Session) -> Sequence[TechStack]:
        """신규 선택에 사용할 활성 기술 스택 목록을 반환한다."""
        return TechStackRepository.list(db)

    @staticmethod
    def find_by_ids(db: Session, ids: set[int]) -> Sequence[TechStack]:
        """식별자에 해당하는 기술 스택을 활성 상태와 관계없이 조회한다."""
        return TechStackRepository.find_by_ids(db, ids)

    @staticmethod
    def validate_active_ids(db: Session, ids: set[int]) -> Sequence[TechStack]:
        """선택한 모든 기술 스택이 존재하고 활성 상태인지 확인한다."""
        items = TechStackRepository.find_by_ids(db, ids)
        found_ids = {item.tech_stack_id for item in items}
        invalid_ids = sorted(
            ids - found_ids | {item.tech_stack_id for item in items if not item.is_active}
        )
        if invalid_ids:
            raise InvalidProfileSelectionError("techStack", invalid_ids)
        return items
