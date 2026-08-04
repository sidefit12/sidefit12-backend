"""Gemini 임베딩 생성·저장과 하이브리드 점수 테스트."""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.internal_processing.embedding_backfill_service import EmbeddingBackfillService
from app.domains.project_embeddings.models import ProjectEmbedding
from app.domains.project_embeddings.service import ProjectEmbeddingService
from app.domains.projects.models import Project
from app.domains.recommendations.service import RecommendationService
from app.domains.user_embeddings.models import UserEmbedding
from app.domains.user_embeddings.service import UserEmbeddingService
from app.domains.user_profiles.models import UserProfile
from app.domains.users.models import User
from app.integrations.gemini_embeddings import GeminiEmbeddingService


def _user_and_project(db: Session) -> tuple[User, Project]:
    user = User(
        email="vector@sidefit.dev",
        password_hash="hash",
        nickname="벡터사용자",
        user_status="ACTIVE",
        system_role="USER",
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.user_id,
            introduction="FastAPI 프로젝트를 찾습니다.",
            onboarding_completed=True,
        )
    )
    project = Project(
        owner_user_id=user.user_id,
        title="FastAPI 프로젝트",
        summary="추천 벡터 테스트",
        description="Python 백엔드 개발",
        work_type="ONLINE",
        recruitment_deadline=datetime(2099, 1, 1, tzinfo=timezone.utc),
        moderation_status="VISIBLE",
    )
    db.add(project)
    db.flush()
    return user, project


def test_embedding_refresh_is_idempotent(db_session: Session, monkeypatch):
    """같은 원문은 Gemini를 다시 호출하지 않고 임베딩 한 건만 유지한다."""
    user, project = _user_and_project(db_session)
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    calls = []

    def fake_embed(text: str, *, task_type: str) -> list[float]:
        calls.append((text, task_type))
        return [1.0] + [0.0] * 767

    monkeypatch.setattr(GeminiEmbeddingService, "embed", fake_embed)
    assert UserEmbeddingService.refresh(db_session, user.user_id)
    assert ProjectEmbeddingService.refresh(db_session, project.project_id)
    assert not UserEmbeddingService.refresh(db_session, user.user_id)
    assert not ProjectEmbeddingService.refresh(db_session, project.project_id)
    assert db_session.query(UserEmbedding).count() == 1
    assert db_session.query(ProjectEmbedding).count() == 1
    assert [task for _, task in calls] == ["RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT"]


def test_hybrid_semantic_score_uses_cosine_similarity(db_session: Session):
    """저장된 두 벡터의 코사인 유사도를 0~1 점수로 변환한다."""
    user, project = _user_and_project(db_session)
    settings = get_settings()
    values = [1 / math.sqrt(2), 1 / math.sqrt(2)] + [0.0] * 766
    db_session.add_all(
        [
            UserEmbedding(
                user_id=user.user_id,
                normalized_text="사용자",
                embedding=values,
                embedding_model=settings.gemini_embedding_model,
                embedding_version=settings.gemini_embedding_version,
                content_hash="a" * 64,
            ),
            ProjectEmbedding(
                project_id=project.project_id,
                normalized_text="프로젝트",
                embedding=values,
                embedding_model=settings.gemini_embedding_model,
                embedding_version=settings.gemini_embedding_version,
                content_hash="b" * 64,
            ),
        ]
    )
    db_session.flush()
    assert RecommendationService._semantic_score(db_session, user.user_id, project.project_id) == 1


def test_embedding_backfill_processes_existing_data_idempotently(db_session: Session, monkeypatch):
    """기존 사용자·프로젝트 전체를 배치 처리하고 재실행 시 건너뛴다."""
    _user_and_project(db_session)
    db_session.commit()
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    monkeypatch.setattr(
        GeminiEmbeddingService,
        "embed",
        lambda _text, *, task_type: [1.0] + [0.0] * 767,
    )

    first = EmbeddingBackfillService.run(db_session, batch_size=1)
    assert first.success
    assert first.user_processed_count == 1
    assert first.project_processed_count == 1

    repeated = EmbeddingBackfillService.run(db_session, batch_size=1)
    assert repeated.success
    assert repeated.user_processed_count == 0
    assert repeated.project_processed_count == 0
    assert repeated.user_skipped_count == 1
    assert repeated.project_skipped_count == 1
