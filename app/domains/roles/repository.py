"""역할 기준정보 조회 repository."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.roles.models import Role


class RoleRepository:
    """역할 목록과 식별자 기반 조회 연산을 제공한다."""

    @staticmethod
    def list(db: Session, *, active_only: bool = True) -> Sequence[Role]:
        """역할 목록을 이름 순서로 조회한다."""
        query = select(Role)
        if active_only:
            query = query.where(Role.is_active.is_(True))
        return db.scalars(query.order_by(Role.role_name)).all()

    @staticmethod
    def find_by_ids(db: Session, ids: set[int]) -> Sequence[Role]:
        """식별자 집합에 해당하는 역할을 조회한다."""
        return db.scalars(select(Role).where(Role.role_id.in_(ids))).all()
