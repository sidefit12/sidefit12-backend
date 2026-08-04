"""사용자 임베딩 생성과 조회 서비스."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.user_embeddings.models import UserEmbedding
from app.domains.user_embeddings.repository import UserEmbeddingRepository
from app.domains.user_profiles.service import ProfileService
from app.integrations.gemini_embeddings import GeminiEmbeddingService


class UserEmbeddingService:
    @staticmethod
    def refresh(db: Session, user_id: int) -> bool:
        """프로필 텍스트가 바뀐 경우에만 사용자 임베딩을 갱신한다."""
        settings = get_settings()
        normalized_text = ProfileService.recommendation_text(db, user_id)
        content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        item = UserEmbeddingRepository.find(db, user_id, settings.gemini_embedding_version)
        if item is not None and item.content_hash == content_hash:
            return False
        vector = GeminiEmbeddingService.embed(normalized_text, task_type="RETRIEVAL_QUERY")
        now = datetime.now(timezone.utc)
        if item is None:
            item = UserEmbedding(
                user_id=user_id,
                normalized_text=normalized_text,
                embedding=vector,
                embedding_model=settings.gemini_embedding_model,
                embedding_version=settings.gemini_embedding_version,
                content_hash=content_hash,
            )
        else:
            item.normalized_text = normalized_text
            item.embedding = vector
            item.embedding_model = settings.gemini_embedding_model
            item.content_hash = content_hash
            item.updated_at = now
        UserEmbeddingRepository.save(db, item)
        return True

    @staticmethod
    def vector(db: Session, user_id: int) -> list[float] | None:
        settings = get_settings()
        item = UserEmbeddingRepository.find(db, user_id, settings.gemini_embedding_version)
        return list(item.embedding) if item is not None else None
