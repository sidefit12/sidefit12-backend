"""사용자 임베딩 데이터 접근 모듈."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.user_embeddings.models import UserEmbedding


class UserEmbeddingRepository:
    @staticmethod
    def find(db: Session, user_id: int, version: str) -> UserEmbedding | None:
        return db.scalar(
            select(UserEmbedding).where(
                UserEmbedding.user_id == user_id,
                UserEmbedding.embedding_version == version,
            )
        )

    @staticmethod
    def save(db: Session, item: UserEmbedding) -> UserEmbedding:
        db.add(item)
        db.flush()
        return item
