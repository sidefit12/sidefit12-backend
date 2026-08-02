"""사용자 프로필 API 요청·응답 schema."""

from datetime import date
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domains.auth.schemas import to_camel


class ProfileModel(BaseModel):
    """프로필 API JSON 필드에 camelCase alias를 적용하는 기본 schema."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class TopicItem(ProfileModel):
    """응답에 포함되는 토픽 기준정보."""

    topic_id: int
    topic_code: str
    topic_name: str
    is_active: bool


class TechStackItem(ProfileModel):
    """응답에 포함되는 기술 스택 기준정보."""

    tech_stack_id: int
    tech_stack_code: str
    tech_stack_name: str
    category: str | None = None
    is_active: bool


class RoleItem(ProfileModel):
    """응답에 포함되는 역할 기준정보."""

    role_id: int
    role_code: str
    role_name: str
    is_active: bool


class CurrentSelection(ProfileModel):
    """온보딩 화면에서 표시할 사용자의 현재 선택값."""

    topic_ids: list[int]
    tech_stack_ids: list[int]
    role_ids: list[int]


class OnboardingOptionsData(ProfileModel):
    """온보딩 기준정보와 현재 선택값."""

    current_selection: CurrentSelection
    topics: list[TopicItem]
    tech_stacks: list[TechStackItem]
    roles: list[RoleItem]


class OnboardingOptionsResponse(ProfileModel):
    """온보딩 선택 정보 조회 응답."""

    success: bool = True
    data: OnboardingOptionsData


class TechStackSelection(ProfileModel):
    """사용자가 저장할 기술 스택 숙련 정보."""

    tech_stack_id: int = Field(gt=0)
    proficiency_level: Literal["LEARNING", "BEGINNER", "INTERMEDIATE", "ADVANCED"]
    experience_months: int = Field(default=0, ge=0)
    is_learning: bool = False


class RoleSelection(ProfileModel):
    """사용자가 저장할 희망 역할 정보."""

    role_id: int = Field(gt=0)
    priority: int = Field(ge=1)
    experience_level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] | None = None


class ProfileFields(ProfileModel):
    """사용자 프로필의 참여 선호 기본 필드."""

    introduction: str | None = Field(default=None, max_length=500)
    career_level: str | None = Field(default=None, max_length=20)
    preferred_work_type: Literal["ONLINE", "OFFLINE", "HYBRID"] | None = None
    preferred_region: str | None = Field(default=None, max_length=100)
    available_start_date: date | None = None
    available_end_date: date | None = None
    available_hours_per_week: int | None = Field(default=None, ge=1, le=168)

    @model_validator(mode="after")
    def validate_available_dates(self):
        """참여 가능 종료일이 시작일보다 빠르지 않은지 확인한다."""
        if (
            self.available_start_date
            and self.available_end_date
            and self.available_end_date < self.available_start_date
        ):
            raise ValueError("availableEndDate must not be earlier than availableStartDate")
        return self


class OnboardingRequest(ProfileFields):
    """온보딩에서 프로필 선택 정보를 한 번에 저장하는 요청."""

    topic_ids: list[int] = Field(min_length=1, max_length=10)
    tech_stacks: list[TechStackSelection] = Field(min_length=1, max_length=20)
    roles: list[RoleSelection] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_unique_selections(self):
        """토픽·기술 스택·역할 식별자와 역할 우선순위의 중복을 차단한다."""
        _ensure_unique(self.topic_ids, "topicIds")
        _ensure_unique([item.tech_stack_id for item in self.tech_stacks], "techStacks")
        _ensure_unique([item.role_id for item in self.roles], "roles")
        _ensure_unique([item.priority for item in self.roles], "role priorities")
        return self


class ProfileUpdateRequest(ProfileFields):
    """닉네임과 기본 프로필 필드를 부분 수정하는 요청."""

    nickname: str | None = Field(default=None, min_length=2, max_length=15)
    external_link_url: AnyHttpUrl | None = None
    profile_image_file_id: int | None = Field(default=None, gt=0)
    public_material_file_id: int | None = Field(default=None, gt=0)

    @field_validator("external_link_url")
    @classmethod
    def validate_external_link(cls, link: AnyHttpUrl | None):
        """외부 링크를 HTTPS 주소로 제한한다."""
        if link is not None and link.scheme != "https":
            raise ValueError("externalLinkUrl must use HTTPS")
        return link


class TopicUpdateRequest(ProfileModel):
    """관심 토픽 목록 교체 요청."""

    topic_ids: list[int] = Field(min_length=1, max_length=10)

    @field_validator("topic_ids")
    @classmethod
    def validate_unique_topic_ids(cls, topic_ids: list[int]):
        """중복 토픽 식별자를 차단한다."""
        _ensure_unique(topic_ids, "topicIds")
        return topic_ids


class TechStackUpdateRequest(ProfileModel):
    """보유 기술 스택 목록 교체 요청."""

    tech_stacks: list[TechStackSelection] = Field(min_length=1, max_length=20)

    @field_validator("tech_stacks")
    @classmethod
    def validate_unique_tech_stacks(cls, items: list[TechStackSelection]):
        """중복 기술 스택 식별자를 차단한다."""
        _ensure_unique([item.tech_stack_id for item in items], "techStacks")
        return items


class RoleUpdateRequest(ProfileModel):
    """희망 역할 목록 교체 요청."""

    roles: list[RoleSelection] = Field(min_length=1, max_length=3)

    @field_validator("roles")
    @classmethod
    def validate_unique_roles(cls, items: list[RoleSelection]):
        """중복 역할과 우선순위를 차단한다."""
        _ensure_unique([item.role_id for item in items], "roles")
        _ensure_unique([item.priority for item in items], "role priorities")
        return items


class ProfileUser(ProfileModel):
    """내 프로필 응답에 포함하는 사용자 기본 정보."""

    user_id: int
    email: str
    nickname: str
    user_status: str
    system_role: str
    onboarding_completed: bool
    profile_image_url: str | None = None


class SelectedTopic(TopicItem):
    """사용자가 선택한 토픽 응답."""

    interest_level: int
    priority: int


class SelectedTechStack(TechStackItem):
    """사용자가 선택한 기술 스택과 숙련 정보 응답."""

    proficiency_level: str
    experience_months: int
    is_learning: bool


class SelectedRole(RoleItem):
    """사용자가 선택한 희망 역할 응답."""

    priority: int
    experience_level: str | None = None


class ProfileData(ProfileFields):
    """본인 프로필 상세 응답 데이터."""

    user: ProfileUser
    profile_image_file_id: int | None = None
    public_material_file_id: int | None = None
    external_link_url: str | None = None
    topics: list[SelectedTopic]
    tech_stacks: list[SelectedTechStack]
    roles: list[SelectedRole]


class ProfileResponse(ProfileModel):
    """본인 프로필 조회·수정 공통 응답."""

    success: bool = True
    data: ProfileData


class PublicProfileData(ProfileModel):
    """비공개 이메일과 참여 선호를 제외한 공개 프로필 데이터."""

    user_id: int
    nickname: str
    introduction: str | None = None
    profile_image_file_id: int | None = None
    public_material_file_id: int | None = None
    external_link_url: str | None = None
    topics: list[SelectedTopic]
    tech_stacks: list[SelectedTechStack]
    roles: list[SelectedRole]


class PublicProfileResponse(ProfileModel):
    """공개 프로필 조회 응답."""

    success: bool = True
    data: PublicProfileData


class TopicSelectionData(ProfileModel):
    """저장된 관심 토픽 목록 응답 데이터."""

    topics: list[SelectedTopic]


class TopicSelectionResponse(ProfileModel):
    """관심 토픽 설정 응답."""

    success: bool = True
    data: TopicSelectionData


class TechStackSelectionData(ProfileModel):
    """저장된 기술 스택 목록 응답 데이터."""

    tech_stacks: list[SelectedTechStack]


class TechStackSelectionResponse(ProfileModel):
    """기술 스택 설정 응답."""

    success: bool = True
    data: TechStackSelectionData


class RoleSelectionData(ProfileModel):
    """저장된 희망 역할 목록 응답 데이터."""

    roles: list[SelectedRole]


class RoleSelectionResponse(ProfileModel):
    """희망 역할 설정 응답."""

    success: bool = True
    data: RoleSelectionData


def _ensure_unique(values: list, field_name: str) -> None:
    """요청 목록에서 중복된 값을 차단한다."""
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
