"""관심 토픽 목록 제공과 선택값 검증 service."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.domains.topics.models import Topic
from app.domains.topics.repository import TopicRepository
from app.domains.users.exceptions import InvalidProfileSelectionError


class TopicService:
    """활성 토픽 조회와 프로필 토픽 선택 검증을 담당한다."""

    @staticmethod
    def list_active(db: Session) -> Sequence[Topic]:
        """신규 선택에 사용할 활성 토픽 목록을 반환한다."""
        return TopicRepository.list(db)

    @staticmethod
    def validate_active_ids(db: Session, ids: set[int]) -> Sequence[Topic]:
        """선택한 모든 토픽이 존재하고 활성 상태인지 확인한다."""
        items = TopicRepository.find_by_ids(db, ids)
        found_ids = {item.topic_id for item in items}
        invalid_ids = sorted(
            ids - found_ids | {item.topic_id for item in items if not item.is_active}
        )
        if invalid_ids:
            raise InvalidProfileSelectionError("topic", invalid_ids)
        return items
