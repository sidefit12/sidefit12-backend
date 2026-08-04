"""규칙 기반 개인화 및 유사 프로젝트 추천 서비스."""

import base64
import json
import math
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.project_embeddings.service import ProjectEmbeddingService
from app.domains.projects.exceptions import ProjectNotFoundError
from app.domains.projects.service import ProjectService
from app.domains.recommendation_reasons.service import RecommendationReasonService
from app.domains.recommendation_results.service import RecommendationResultService
from app.domains.recommendations.exceptions import InvalidRecommendationCursorError
from app.domains.recommendations.schemas import (
    AsyncJobData,
    CursorMeta,
    ProjectListData,
    RecommendationItem,
    RecommendationPageData,
    RecommendationReasonData,
)
from app.domains.user_embeddings.service import UserEmbeddingService
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User


class RecommendationService:
    """RECO-001~003 추천 규칙을 제공한다."""

    VERSION = "hybrid-v1"

    @staticmethod
    def page(db: Session, user: User, *, cursor: str | None, size: int):
        """개인화 결과 또는 온보딩 미완성 대체 목록을 커서 방식으로 반환한다."""
        offset = RecommendationService._decode_cursor(cursor)
        profile = ProfileService.recommendation_profile(db, user.user_id)
        candidates = RecommendationService._candidates(db, user)
        fallback = not profile["onboarding_completed"]
        if fallback:
            all_items = [RecommendationService._fallback_item(db, user, p) for p in candidates]
            fallback_reason = "ONBOARDING_INCOMPLETE"
        else:
            all_items = RecommendationService._personalized_items(db, user, profile, candidates)
            fallback_reason = None
        selected = all_items[offset : offset + size]
        has_next = offset + size < len(all_items)
        next_cursor = RecommendationService._encode_cursor(offset + size) if has_next else None
        return (
            RecommendationPageData(
                items=selected, fallback=fallback, fallback_reason=fallback_reason
            ),
            CursorMeta(next_cursor=next_cursor, has_next=has_next),
        )

    @staticmethod
    def top(db: Session, user: User, size: int) -> list[RecommendationItem]:
        """홈 화면에 첫 추천 항목을 제공한다."""
        data, _ = RecommendationService.page(db, user, cursor=None, size=size)
        return data.items

    @staticmethod
    def similar(db: Session, project_id: int, viewer: User | None, size: int) -> ProjectListData:
        """토픽·기술·역할 공통 항목을 기준으로 유사 프로젝트를 반환한다."""
        base = ProjectService.find_visible(db, project_id, viewer)
        if base is None:
            raise ProjectNotFoundError(project_id)
        base_data = ProjectService.match_data(db, project_id)
        scored = []
        for candidate in ProjectService.recommendation_candidates(db, None):
            if candidate.project_id == project_id:
                continue
            data = ProjectService.match_data(db, candidate.project_id)
            score = sum(
                len(base_data[key] & data[key]) / max(len(base_data[key] | data[key]), 1)
                for key in ("topic_ids", "tech_stack_ids", "role_ids")
            )
            scored.append((score, candidate))
        scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return ProjectListData(
            items=[ProjectService.card(db, project, viewer) for _, project in scored[:size]]
        )

    @staticmethod
    def refresh(db: Session, user: User, force: bool) -> AsyncJobData:
        """기존 추천 결과를 무효화해 다음 조회에서 다시 계산하도록 한다."""
        if force or RecommendationResultService.list_by_user(
            db, user.user_id, RecommendationService.VERSION
        ):
            RecommendationResultService.delete_by_user(db, user.user_id)
            db.commit()
        return AsyncJobData(job_id=f"job_{uuid4().hex}", status="QUEUED")

    @staticmethod
    def _personalized_items(db, user, profile, candidates) -> list[RecommendationItem]:
        existing = RecommendationResultService.list_by_user(
            db, user.user_id, RecommendationService.VERSION
        )
        by_project = {result.project_id: result for result in existing}
        items = []
        for project in candidates:
            result = by_project.get(project.project_id)
            if result is None:
                result = RecommendationService._calculate(db, user, profile, project)
            reasons = RecommendationReasonService.list_by_result(
                db, result.recommendation_result_id
            )
            items.append(
                RecommendationItem(
                    recommendation_result_id=result.recommendation_result_id,
                    project=ProjectService.card(db, project, user),
                    rule_score=float(result.rule_score),
                    semantic_score=(
                        float(result.semantic_score) if result.semantic_score is not None else None
                    ),
                    final_score=float(result.final_score),
                    recommendation_version=result.recommendation_version,
                    reasons=[
                        RecommendationReasonData.model_validate(reason, from_attributes=True)
                        for reason in reasons[:3]
                    ],
                )
            )
        db.commit()
        return sorted(
            items, key=lambda item: (item.final_score, item.project.project_id), reverse=True
        )

    @staticmethod
    def _calculate(db, user, profile, project):
        data = ProjectService.match_data(db, project.project_id)
        role = bool(profile["role_ids"] & data["role_ids"])
        topic = bool(profile["topic_ids"] & data["topic_ids"])
        tech = bool(profile["tech_stack_ids"] & data["tech_stack_ids"])
        score = (0.4 if role else 0) + (0.3 if topic else 0) + (0.3 if tech else 0)
        semantic_score = RecommendationService._semantic_score(db, user.user_id, project.project_id)
        final_score = score if semantic_score is None else score * 0.7 + semantic_score * 0.3
        now = datetime.now(timezone.utc)
        result = RecommendationResultService.create(
            db,
            user_id=user.user_id,
            project_id=project.project_id,
            rule_score=score,
            semantic_score=semantic_score,
            final_score=final_score,
            version=RecommendationService.VERSION,
            generated_at=now,
            expires_at=now + timedelta(hours=6),
        )
        card = ProjectService.card(db, project, user)
        reasons = []
        if role:
            reasons.append(("MATCHED_ROLE", "희망 역할과 일치하는 포지션을 모집하고 있어요.", 0.4))
        if topic:
            reasons.append(
                (
                    "MATCHED_TOPIC",
                    f"관심 토픽인 {card.topics[0].topic_name}과 관련된 프로젝트예요.",
                    0.3,
                )
            )
        if tech:
            reasons.append(
                (
                    "MATCHED_TECH_STACK",
                    f"보유 기술인 {card.tech_stacks[0].tech_stack_name}을 활용할 수 있어요.",
                    0.3,
                )
            )
        if semantic_score is not None and semantic_score > 0:
            reasons.append(
                (
                    "SEMANTIC_SIMILARITY",
                    "프로필 내용과 프로젝트 모집 내용의 의미가 유사해요.",
                    semantic_score * 0.3,
                )
            )
        if not reasons:
            reasons.append(("COLD_START", "새롭게 등록된 모집 중 프로젝트예요.", 0.0))
        RecommendationReasonService.create_all(db, result.recommendation_result_id, reasons[:3])
        db.flush()
        return result

    @staticmethod
    def _semantic_score(db: Session, user_id: int, project_id: int) -> float | None:
        """저장된 사용자·프로젝트 벡터의 코사인 유사도를 0~1 범위로 반환한다."""
        user_vector = UserEmbeddingService.vector(db, user_id)
        project_vector = ProjectEmbeddingService.vector(db, project_id)
        if user_vector is None or project_vector is None or len(user_vector) != len(project_vector):
            return None
        denominator = math.sqrt(sum(x * x for x in user_vector)) * math.sqrt(
            sum(x * x for x in project_vector)
        )
        if denominator == 0:
            return None
        cosine = sum(x * y for x, y in zip(user_vector, project_vector, strict=True)) / denominator
        return min(max((cosine + 1) / 2, 0), 1)

    @staticmethod
    def _fallback_item(db, user, project):
        return RecommendationItem(
            project=ProjectService.card(db, project, user),
            rule_score=0,
            semantic_score=None,
            final_score=0,
            recommendation_version="fallback-v1",
            reasons=[
                RecommendationReasonData(
                    reason_type="COLD_START",
                    reason_text="최근 등록된 모집 중 프로젝트예요.",
                    contribution_score=0,
                )
            ],
        )

    @staticmethod
    def _candidates(db, user):
        now = datetime.now(timezone.utc)
        return [
            p
            for p in ProjectService.recommendation_candidates(db, user)
            if RecommendationService._utc(p.recruitment_deadline) > now
        ]

    @staticmethod
    def _utc(value):
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )

    @staticmethod
    def _encode_cursor(offset: int) -> str:
        return base64.urlsafe_b64encode(json.dumps({"offset": offset}).encode()).decode()

    @staticmethod
    def _decode_cursor(cursor: str | None) -> int:
        if cursor is None:
            return 0
        try:
            value = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())["offset"]
            if not isinstance(value, int) or value < 0:
                raise ValueError
            return value
        except Exception as exc:
            raise InvalidRecommendationCursorError() from exc
