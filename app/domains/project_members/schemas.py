"""프로젝트 팀원 API 요청·응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.auth.schemas import to_camel


class MemberModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class MemberLeaveRequest(MemberModel):
    reason: str | None = Field(default=None, max_length=1000, description="프로젝트 탈퇴 사유")


class MemberRemoveRequest(MemberModel):
    reason: str = Field(
        min_length=10,
        max_length=1000,
        description="공백 제거 기준 10자 이상의 팀원 퇴출 사유",
        examples=["지속적인 무단 불참으로 팀에서 제외합니다."],
    )

    @field_validator("reason")
    @classmethod
    def validate_trimmed_reason(cls, value: str) -> str:
        if len(value.strip()) < 10:
            raise ValueError("팀원 퇴출 사유는 공백 제거 기준 10자 이상이어야 합니다.")
        return value.strip()


class MemberRestoreRequest(MemberModel):
    reason: str | None = Field(default=None, max_length=1000, description="팀원 복구 사유")


class MemberUserSummary(MemberModel):
    user_id: int
    nickname: str
    user_status: str
    system_role: str
    onboarding_completed: bool
    profile_image_url: str | None = None
    email: str | None = None


class MemberResource(MemberModel):
    project_member_id: int
    project_id: int
    project_position_id: int | None
    member_type: str
    member_status: str
    joined_at: datetime
    left_at: datetime | None = None
    user: MemberUserSummary


class ChannelResource(MemberModel):
    project_collaboration_channel_id: int
    channel_type: str
    channel_name: str
    channel_url: str


class PositionCapacity(MemberModel):
    project_position_id: int
    position_title: str
    required_count: int
    active_count: int
    position_status: str


class MemberListData(MemberModel):
    items: list[MemberResource]
    position_summary: dict[str, PositionCapacity]
    channels: list[ChannelResource] | None = None


class MemberListResponse(MemberModel):
    success: bool = True
    data: MemberListData
    request_id: str | None = None


class MemberData(MemberModel):
    member: MemberResource


class MemberResponse(MemberModel):
    success: bool = True
    data: MemberData
    request_id: str | None = None


class MemberEventResource(MemberModel):
    event_type: str
    reason: str | None = None
    created_at: datetime
    actor: MemberUserSummary | None = None


class MemberEventPageData(MemberModel):
    items: list[MemberEventResource]


class PageMeta(MemberModel):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class MemberEventPageResponse(MemberModel):
    success: bool = True
    data: MemberEventPageData
    meta: PageMeta
    request_id: str | None = None
