"""프로젝트 지원 API 요청·응답 스키마."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel
from app.domains.user_profiles.schemas import PublicProfileData

ApplicationStatus = Literal["PENDING", "ACCEPTED", "REJECTED", "CANCELED"]


class ApplicationModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ApplicationCreateRequest(ApplicationModel):
    application_message: str = Field(
        min_length=20,
        max_length=1000,
        description="지원 메시지",
        examples=["백엔드 API 개발 경험으로 프로젝트에 기여하겠습니다."],
    )
    project_position_id: int = Field(gt=0, description="지원할 모집 포지션 식별자", examples=[21])


class ApplicationCancelRequest(ApplicationModel):
    reason: str | None = Field(default=None, max_length=500, description="지원 취소 메모")


class ApplicationAcceptRequest(ApplicationModel):
    note: str | None = Field(default=None, max_length=500, description="지원 승인 메모")


class ApplicationRejectRequest(ApplicationModel):
    rejection_reason_code: str = Field(
        min_length=1,
        max_length=50,
        description="서비스에서 정의한 거절 사유 코드",
        examples=["ROLE_MISMATCH"],
    )
    rejection_reason: str | None = Field(default=None, max_length=500, description="추가 거절 사유")


class ApplicantSummary(ApplicationModel):
    user_id: int = Field(description="지원자 식별자")
    nickname: str = Field(description="지원자 닉네임")


class ApplicationResource(ApplicationModel):
    application_id: int
    project_id: int
    project_title: str
    project_position_id: int
    application_message: str | None = None
    application_status: ApplicationStatus
    applied_at: datetime
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    applicant: ApplicantSummary


class ApplicationResponse(ApplicationModel):
    success: bool = True
    data: ApplicationResource
    request_id: str | None = None


class PageMeta(ApplicationModel):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class ApplicationPageData(ApplicationModel):
    items: list[ApplicationResource]
    status_counts: dict[str, int]


class ApplicationPageResponse(ApplicationModel):
    success: bool = True
    data: ApplicationPageData
    meta: PageMeta
    request_id: str | None = None


class ApplicationDetailData(ApplicationModel):
    applicant_profile: PublicProfileData
    application: ApplicationResource
    submitted_snapshot: dict[str, Any] | None = None


class ApplicationDetailResponse(ApplicationModel):
    success: bool = True
    data: ApplicationDetailData
    request_id: str | None = None


class MemberUserSummary(ApplicationModel):
    user_id: int
    nickname: str
    user_status: str
    system_role: str
    onboarding_completed: bool
    profile_image_url: str | None = None
    email: str | None = None


class MemberResource(ApplicationModel):
    project_member_id: int
    project_id: int
    project_position_id: int
    member_type: str
    member_status: str
    joined_at: datetime
    left_at: datetime | None = None
    user: MemberUserSummary


class PositionSummary(ApplicationModel):
    required_count: int
    accepted_count: int
    position_status: str


class ApplicationDecisionData(ApplicationModel):
    application: ApplicationResource
    member: MemberResource | None = None
    position_summary: PositionSummary


class ApplicationDecisionResponse(ApplicationModel):
    success: bool = True
    data: ApplicationDecisionData
    request_id: str | None = None
