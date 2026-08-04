"""추천 API 요청 및 응답 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel
from app.domains.projects.schemas import ProjectCard


class RecommendationModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RecommendationReasonData(RecommendationModel):
    reason_type: str = Field(description="추천 이유 유형")
    reason_text: str = Field(description="추천 이유 설명")
    contribution_score: float | None = Field(default=None, description="추천 점수 기여도")


class RecommendationItem(RecommendationModel):
    recommendation_result_id: int | None = Field(
        default=None, description="저장된 추천 결과 식별자"
    )
    project: ProjectCard
    rule_score: float = Field(ge=0, le=1, description="규칙 기반 추천 점수")
    semantic_score: float | None = Field(default=None, ge=0, le=1, description="의미 유사도 점수")
    final_score: float = Field(ge=0, le=1, description="최종 추천 점수")
    recommendation_version: str = Field(description="추천 알고리즘 버전")
    reasons: list[RecommendationReasonData] = Field(description="최대 3개의 추천 이유")


class RecommendationPageData(RecommendationModel):
    items: list[RecommendationItem]
    fallback: bool = Field(description="대체 추천 목록 여부")
    fallback_reason: str | None = Field(default=None, description="대체 추천 적용 사유")


class CursorMeta(RecommendationModel):
    next_cursor: str | None = None
    has_next: bool


class RecommendationPageResponse(RecommendationModel):
    success: bool = True
    data: RecommendationPageData
    meta: CursorMeta
    request_id: str | None = None


class ProjectListData(RecommendationModel):
    items: list[ProjectCard]


class ProjectListResponse(RecommendationModel):
    success: bool = True
    data: ProjectListData
    request_id: str | None = None


class RecommendationRefreshRequest(RecommendationModel):
    force: bool = Field(default=False, description="기존 결과가 있어도 강제로 무효화할지 여부")


class AsyncJobData(RecommendationModel):
    job_id: str = Field(description="추천 재계산 작업 식별자")
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED"] = Field(description="작업 상태")


class AsyncJobResponse(RecommendationModel):
    success: bool = True
    data: AsyncJobData
    request_id: str | None = None
