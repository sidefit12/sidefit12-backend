"""기술 스택 기준정보 조회 repository."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.tech_stacks.models import TechStack


class TechStackRepository:
    """기술 스택 목록과 식별자 기반 조회 연산을 제공한다."""

    @staticmethod
    def list(
        db: Session, *, active_only: bool = True, keyword: str | None = None
    ) -> Sequence[TechStack]:
        """기술 스택 목록을 분류와 이름 순서로 조회한다."""
        query = select(TechStack)
        if active_only:
            query = query.where(TechStack.is_active.is_(True))
        if keyword:
            pattern = f"%{keyword.strip()}%"
            query = query.where(
                TechStack.tech_stack_code.ilike(pattern) | TechStack.tech_stack_name.ilike(pattern)
            )
        return db.scalars(query.order_by(TechStack.category, TechStack.tech_stack_name)).all()

    @staticmethod
    def find_by_ids(db: Session, ids: set[int]) -> Sequence[TechStack]:
        """식별자 집합에 해당하는 기술 스택을 조회한다."""
        return db.scalars(select(TechStack).where(TechStack.tech_stack_id.in_(ids))).all()
