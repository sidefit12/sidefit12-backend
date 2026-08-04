"""기존 사용자·프로젝트 임베딩 일괄 백필 서비스."""

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domains.internal_processing.schemas import EmbeddingBackfillResult
from app.domains.project_embeddings.service import ProjectEmbeddingService
from app.domains.projects.service import ProjectService
from app.domains.user_embeddings.service import UserEmbeddingService
from app.domains.users.service import UserService


class EmbeddingBackfillService:
    """기존 추천 대상의 임베딩을 커서 배치 방식으로 생성한다."""

    @staticmethod
    def run(db: Session, *, batch_size: int = 50) -> EmbeddingBackfillResult:
        """사용자와 프로젝트를 순회하며 변경된 임베딩만 저장한다."""
        if not 1 <= batch_size <= 500:
            raise ValueError("batch_size는 1 이상 500 이하여야 합니다.")
        if not get_settings().gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY가 설정되지 않았습니다.")

        result = EmbeddingBackfillResult()
        EmbeddingBackfillService._backfill_users(db, result, batch_size)
        EmbeddingBackfillService._backfill_projects(db, result, batch_size)
        failed = result.user_failed_count + result.project_failed_count
        processed = result.user_processed_count + result.project_processed_count
        result.success = failed == 0
        if failed == 0:
            result.result = "SUCCESS"
        elif processed == 0:
            result.result = "FAILED"
        else:
            result.result = "PARTIAL_SUCCESS"
        return result

    @staticmethod
    def _backfill_users(db: Session, result: EmbeddingBackfillResult, batch_size: int) -> None:
        after_id = 0
        while True:
            user_ids = UserService.list_embedding_target_ids(
                db, after_user_id=after_id, limit=batch_size
            )
            if not user_ids:
                return
            for user_id in user_ids:
                try:
                    changed = UserEmbeddingService.refresh(db, user_id)
                    db.commit()
                    if changed:
                        result.user_processed_count += 1
                    else:
                        result.user_skipped_count += 1
                except Exception:
                    db.rollback()
                    result.user_failed_count += 1
            after_id = user_ids[-1]

    @staticmethod
    def _backfill_projects(db: Session, result: EmbeddingBackfillResult, batch_size: int) -> None:
        after_id = 0
        while True:
            project_ids = ProjectService.list_embedding_target_ids(
                db, after_project_id=after_id, limit=batch_size
            )
            if not project_ids:
                return
            for project_id in project_ids:
                try:
                    changed = ProjectEmbeddingService.refresh(db, project_id)
                    db.commit()
                    if changed:
                        result.project_processed_count += 1
                    else:
                        result.project_skipped_count += 1
                except Exception:
                    db.rollback()
                    result.project_failed_count += 1
            after_id = project_ids[-1]
