"""프로젝트 임베딩 생성과 조회 서비스."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.project_embeddings.models import ProjectEmbedding
from app.domains.project_embeddings.repository import ProjectEmbeddingRepository
from app.domains.projects.service import ProjectService
from app.integrations.gemini_embeddings import GeminiEmbeddingService


class ProjectEmbeddingService:
    @staticmethod
    def refresh(db: Session, project_id: int) -> bool:
        """프로젝트 텍스트가 바뀐 경우에만 프로젝트 임베딩을 갱신한다."""
        settings = get_settings()
        normalized_text = ProjectService.recommendation_text(db, project_id)
        content_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
        item = ProjectEmbeddingRepository.find(db, project_id, settings.gemini_embedding_version)
        if item is not None and item.content_hash == content_hash:
            return False
        vector = GeminiEmbeddingService.embed(normalized_text, task_type="RETRIEVAL_DOCUMENT")
        now = datetime.now(timezone.utc)
        if item is None:
            item = ProjectEmbedding(
                project_id=project_id,
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
        ProjectEmbeddingRepository.save(db, item)
        return True

    @staticmethod
    def vector(db: Session, project_id: int) -> list[float] | None:
        settings = get_settings()
        item = ProjectEmbeddingRepository.find(db, project_id, settings.gemini_embedding_version)
        return list(item.embedding) if item is not None else None
