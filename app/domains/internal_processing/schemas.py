"""내부 처리 입력과 결과 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.auth.schemas import to_camel


class InternalModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class InternalResult(InternalModel):
    success: bool = True
    processed_count: int = 0
    failed_count: int = 0
    result: Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILED"] = "SUCCESS"
    request_id: str | None = None


class EmbeddingBackfillResult(InternalModel):
    """사용자·프로젝트 임베딩 백필 실행 결과."""

    success: bool = True
    user_processed_count: int = 0
    user_skipped_count: int = 0
    user_failed_count: int = 0
    project_processed_count: int = 0
    project_skipped_count: int = 0
    project_failed_count: int = 0
    result: Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILED"] = "SUCCESS"


class RecommendationUpdateEvent(InternalModel):
    target_type: Literal["USER", "PROJECT"] = Field(description="변경 대상 유형")
    target_id: int = Field(gt=0, description="변경 대상 식별자")
    model_version: str = Field(
        default="normalized-v1", min_length=1, max_length=50, description="추천 처리 버전"
    )


class DomainNotificationEvent(InternalModel):
    event_type: Literal[
        "APPLICATION_RECEIVED",
        "APPLICATION_ACCEPTED",
        "APPLICATION_REJECTED",
        "RECRUITMENT_CLOSED",
        "MEMBER_LEFT",
        "MEMBER_REMOVED",
        "MEMBER_RESTORED",
    ]
    recipient_user_id: int = Field(gt=0, description="알림 수신 사용자 식별자")
    application_id: int | None = Field(None, gt=0, description="관련 지원 식별자")
    project_id: int | None = Field(None, gt=0, description="관련 프로젝트 식별자")

    @model_validator(mode="after")
    def validate_reference(self):
        if self.event_type.startswith("APPLICATION_") and self.application_id is None:
            raise ValueError("지원 이벤트에는 applicationId가 필요합니다.")
        if not self.event_type.startswith("APPLICATION_") and self.project_id is None:
            raise ValueError("프로젝트 이벤트에는 projectId가 필요합니다.")
        return self
