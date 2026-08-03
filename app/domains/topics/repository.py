"""관심 토픽 기준정보 조회 repository."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.topics.models import Topic


class TopicRepository:
    """토픽 목록과 식별자 기반 조회 연산을 제공한다."""

    @staticmethod
    def list(
        db: Session, *, active_only: bool = True, keyword: str | None = None
    ) -> Sequence[Topic]:
        """토픽 목록을 이름 순서로 조회한다."""
        query = select(Topic)
        if active_only:
            query = query.where(Topic.is_active.is_(True))
        if keyword:
            pattern = f"%{keyword.strip()}%"
            query = query.where(Topic.topic_code.ilike(pattern) | Topic.topic_name.ilike(pattern))
        return db.scalars(query.order_by(Topic.topic_name)).all()

    @staticmethod
    def find_by_ids(db: Session, ids: set[int]) -> Sequence[Topic]:
        """식별자 집합에 해당하는 토픽을 조회한다."""
        return db.scalars(select(Topic).where(Topic.topic_id.in_(ids))).all()
