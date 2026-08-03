"""프로젝트 API 요청·응답 스키마."""

from datetime import date, datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator

from app.domains.auth.schemas import to_camel


class ProjectModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ProjectTopicInput(ProjectModel):
    topic_id: int = Field(gt=0)
    is_primary: bool = False


class ProjectTechStackInput(ProjectModel):
    tech_stack_id: int = Field(gt=0)
    requirement_type: Literal["REQUIRED", "PREFERRED"]
    required_level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] | None = None


class ProjectPositionInput(ProjectModel):
    role_id: int = Field(gt=0)
    position_title: str = Field(min_length=1, max_length=100)
    responsibilities: str | None = Field(default=None, max_length=2000)
    required_count: int = Field(gt=0, le=100)
    required_level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] | None = None


class CollaborationChannelInput(ProjectModel):
    channel_type: Literal["DISCORD", "KAKAO_OPEN_CHAT", "SLACK", "NOTION", "OTHER"]
    channel_name: str = Field(min_length=1, max_length=100)
    channel_url: AnyHttpUrl


class ProjectFields(ProjectModel):
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=2, max_length=500)
    description: str = Field(min_length=10, max_length=20000)
    work_type: Literal["ONLINE", "OFFLINE", "HYBRID"]
    region: str | None = Field(default=None, max_length=100)
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    weekly_hours: int | None = Field(default=None, ge=1, le=168)
    recruitment_deadline: datetime
    recruitment_status: Literal["DRAFT", "RECRUITING", "CLOSED"] = "DRAFT"
    visibility: Literal["PUBLIC", "PRIVATE"] = "PUBLIC"

    @model_validator(mode="after")
    def validate_project(self):
        if (
            self.expected_start_date
            and self.expected_end_date
            and self.expected_end_date < self.expected_start_date
        ):
            raise ValueError("예상 종료일은 예상 시작일보다 빠를 수 없습니다.")
        if self.work_type == "OFFLINE" and not (self.region and self.region.strip()):
            raise ValueError("오프라인 프로젝트에는 지역이 필요합니다.")
        return self


class ProjectCreateRequest(ProjectFields):
    topics: list[ProjectTopicInput] = Field(min_length=1, max_length=10)
    tech_stacks: list[ProjectTechStackInput] = Field(default_factory=list, max_length=20)
    positions: list[ProjectPositionInput] = Field(min_length=1, max_length=10)
    collaboration_channels: list[CollaborationChannelInput] = Field(
        default_factory=list, max_length=10
    )

    @model_validator(mode="after")
    def validate_relations(self):
        _unique([item.topic_id for item in self.topics], "topics")
        _unique([item.tech_stack_id for item in self.tech_stacks], "techStacks")
        _unique([item.role_id for item in self.positions], "positions")
        if sum(item.is_primary for item in self.topics) > 1:
            raise ValueError("대표 토픽은 하나만 선택할 수 있습니다.")
        return self


class ProjectUpdateRequest(ProjectModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    summary: str | None = Field(default=None, min_length=2, max_length=500)
    description: str | None = Field(default=None, min_length=10, max_length=20000)
    work_type: Literal["ONLINE", "OFFLINE", "HYBRID"] | None = None
    region: str | None = Field(default=None, max_length=100)
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    weekly_hours: int | None = Field(default=None, ge=1, le=168)
    recruitment_deadline: datetime | None = None
    recruitment_status: Literal["DRAFT", "RECRUITING", "CLOSED"] | None = None
    project_status: Literal["PREPARING", "IN_PROGRESS", "COMPLETED", "CANCELED"] | None = None
    visibility: Literal["PUBLIC", "PRIVATE"] | None = None
    topics: list[ProjectTopicInput] | None = Field(default=None, min_length=1, max_length=10)
    tech_stacks: list[ProjectTechStackInput] | None = Field(default=None, max_length=20)
    positions: list[ProjectPositionInput] | None = Field(default=None, min_length=1, max_length=10)
    collaboration_channels: list[CollaborationChannelInput] | None = Field(
        default=None, max_length=10
    )

    @model_validator(mode="after")
    def validate_relations(self):
        if self.topics is not None:
            _unique([item.topic_id for item in self.topics], "topics")
            if sum(item.is_primary for item in self.topics) > 1:
                raise ValueError("대표 토픽은 하나만 선택할 수 있습니다.")
        if self.tech_stacks is not None:
            _unique([item.tech_stack_id for item in self.tech_stacks], "techStacks")
        if self.positions is not None:
            _unique([item.role_id for item in self.positions], "positions")
        return self


class ProjectDeleteRequest(ProjectModel):
    reason: str = Field(min_length=5, max_length=500)


class TopicData(ProjectModel):
    topic_id: int
    topic_code: str
    topic_name: str
    is_primary: bool


class TechStackData(ProjectModel):
    tech_stack_id: int
    tech_stack_code: str
    tech_stack_name: str
    requirement_type: str
    required_level: str | None


class PositionData(ProjectModel):
    project_position_id: int
    role_id: int
    role_code: str
    role_name: str
    position_title: str
    responsibilities: str | None
    required_count: int
    required_level: str | None
    position_status: str


class CollaborationChannelData(ProjectModel):
    project_collaboration_channel_id: int
    channel_type: str
    channel_name: str
    channel_url: str
    is_active: bool


class OwnerData(ProjectModel):
    user_id: int
    nickname: str


class ProjectData(ProjectFields):
    project_id: int
    owner: OwnerData
    project_status: str
    view_count: int
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    topics: list[TopicData]
    tech_stacks: list[TechStackData]
    positions: list[PositionData]
    collaboration_channels: list[CollaborationChannelData]


class ProjectResponse(ProjectModel):
    success: bool = True
    data: ProjectData


class ProjectListData(ProjectModel):
    items: list[ProjectData]
    page: int
    size: int
    total: int
    total_pages: int


class ProjectListResponse(ProjectModel):
    success: bool = True
    data: ProjectListData


class ProjectDeleteData(ProjectModel):
    project_id: int
    deleted: bool = True


class ProjectDeleteResponse(ProjectModel):
    success: bool = True
    data: ProjectDeleteData


def _unique(values: list[int], field: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field}에 중복 항목을 포함할 수 없습니다.")
