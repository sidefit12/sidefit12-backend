"""프로젝트 임베딩 데이터 접근 모듈."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.project_embeddings.models import ProjectEmbedding


class ProjectEmbeddingRepository:
    @staticmethod
    def find(db: Session, project_id: int, version: str) -> ProjectEmbedding | None:
        return db.scalar(
            select(ProjectEmbedding).where(
                ProjectEmbedding.project_id == project_id,
                ProjectEmbedding.embedding_version == version,
            )
        )

    @staticmethod
    def save(db: Session, item: ProjectEmbedding) -> ProjectEmbedding:
        db.add(item)
        db.flush()
        return item
