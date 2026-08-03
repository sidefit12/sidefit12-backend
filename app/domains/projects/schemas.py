"""프로젝트 API 요청·응답 스키마."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.auth.schemas import to_camel


class ProjectModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ProjectTechStackInput(ProjectModel):
    tech_stack_id: int = Field(gt=0, description="기술 스택 식별자", examples=[4])
    requirement_type: Literal["REQUIRED", "PREFERRED"] = Field(
        description="기술 요구 구분", examples=["REQUIRED"]
    )
    required_level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] | None = Field(
        default=None, description="요구 숙련도", examples=["BEGINNER"]
    )


class ProjectPositionInput(ProjectModel):
    project_position_id: int | None = Field(
        default=None, gt=0, description="수정할 기존 모집 포지션 식별자", examples=[21]
    )
    role_id: int = Field(gt=0, description="모집 역할 식별자", examples=[2])
    position_title: str = Field(
        min_length=1, max_length=100, description="모집 포지션명", examples=["백엔드 개발자"]
    )
    responsibilities: str | None = Field(
        default=None, max_length=2000, description="담당 업무", examples=["API와 DB 설계"]
    )
    required_count: int = Field(default=1, gt=0, le=20, description="모집 인원", examples=[2])
    required_level: Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"] | None = Field(
        default=None, description="요구 경험 수준", examples=["BEGINNER"]
    )


class ProjectCreateRequest(ProjectModel):
    title: str = Field(min_length=5, max_length=100, description="프로젝트 제목")
    summary: str = Field(min_length=10, max_length=500, description="프로젝트 요약")
    description: str = Field(min_length=20, max_length=5000, description="프로젝트 상세 설명")
    work_type: Literal["ONLINE", "OFFLINE", "HYBRID"] = Field(description="프로젝트 진행 방식")
    region: str | None = Field(default=None, max_length=100, description="프로젝트 진행 지역")
    expected_start_date: date | None = Field(default=None, description="예상 시작일")
    expected_end_date: date | None = Field(default=None, description="예상 종료일")
    weekly_hours: int | None = Field(default=None, ge=1, le=168, description="주당 예상 참여 시간")
    recruitment_deadline: datetime = Field(description="모집 마감 일시")
    visibility: Literal["PUBLIC", "PRIVATE"] = Field(
        default="PUBLIC", description="프로젝트 공개 범위"
    )
    topic_ids: list[int] = Field(
        min_length=1, max_length=10, description="프로젝트 토픽 식별자 목록"
    )
    tech_stacks: list[ProjectTechStackInput] = Field(
        default_factory=list, max_length=20, description="프로젝트 필요 기술 목록"
    )
    positions: list[ProjectPositionInput] = Field(
        min_length=1, max_length=20, description="프로젝트 모집 포지션 목록"
    )

    @model_validator(mode="after")
    def validate_request(self):
        _unique(self.topic_ids, "topicIds")
        _unique([x.tech_stack_id for x in self.tech_stacks], "techStacks")
        _unique([x.role_id for x in self.positions], "positions")
        if sum(x.required_count for x in self.positions) > 20:
            raise ValueError("전체 모집 인원은 20명을 초과할 수 없습니다.")
        if (
            self.expected_start_date
            and self.expected_end_date
            and self.expected_end_date < self.expected_start_date
        ):
            raise ValueError("예상 종료일은 예상 시작일보다 빠를 수 없습니다.")
        if self.work_type in {"OFFLINE", "HYBRID"} and not (self.region and self.region.strip()):
            raise ValueError("오프라인 또는 혼합 프로젝트에는 지역이 필요합니다.")
        return self


class ProjectUpdateRequest(ProjectModel):
    title: str | None = Field(
        default=None, min_length=5, max_length=100, description="변경할 프로젝트 제목"
    )
    summary: str | None = Field(
        default=None, min_length=10, max_length=500, description="변경할 프로젝트 요약"
    )
    description: str | None = Field(
        default=None, min_length=20, max_length=5000, description="변경할 프로젝트 상세 설명"
    )
    work_type: Literal["ONLINE", "OFFLINE", "HYBRID"] | None = Field(
        default=None, description="변경할 진행 방식"
    )
    region: str | None = Field(default=None, max_length=100, description="변경할 진행 지역")
    expected_start_date: date | None = Field(default=None, description="변경할 예상 시작일")
    expected_end_date: date | None = Field(default=None, description="변경할 예상 종료일")
    weekly_hours: int | None = Field(
        default=None, ge=1, le=168, description="변경할 주당 예상 시간"
    )
    recruitment_deadline: datetime | None = Field(default=None, description="변경할 모집 마감 일시")
    visibility: Literal["PUBLIC", "PRIVATE"] | None = Field(
        default=None, description="변경할 공개 범위"
    )
    topic_ids: list[int] | None = Field(
        default=None, min_length=1, max_length=10, description="교체할 토픽 식별자 목록"
    )
    tech_stacks: list[ProjectTechStackInput] | None = Field(
        default=None, max_length=20, description="교체할 필요 기술 목록"
    )
    positions: list[ProjectPositionInput] | None = Field(
        default=None, min_length=1, max_length=20, description="교체할 모집 포지션 목록"
    )

    @model_validator(mode="after")
    def validate_request(self):
        if self.topic_ids is not None:
            _unique(self.topic_ids, "topicIds")
        if self.tech_stacks is not None:
            _unique([x.tech_stack_id for x in self.tech_stacks], "techStacks")
        if self.positions is not None:
            _unique([x.role_id for x in self.positions], "positions")
            if sum(x.required_count for x in self.positions) > 20:
                raise ValueError("전체 모집 인원은 20명을 초과할 수 없습니다.")
        return self


class ProjectDeleteRequest(ProjectModel):
    deletion_reason: str = Field(min_length=10, max_length=500, description="프로젝트 삭제 사유")


class RecruitmentStatusRequest(ProjectModel):
    recruitment_status: Literal["RECRUITING", "CLOSED"] = Field(description="변경할 모집 상태")
    new_deadline: datetime | None = Field(
        default=None, description="모집 재개 시 적용할 새 마감 일시"
    )


class ProjectStatusRequest(ProjectModel):
    project_status: Literal["PREPARING", "IN_PROGRESS", "COMPLETED", "CANCELED"] = Field(
        description="변경할 프로젝트 진행 상태"
    )
    reason: str | None = Field(default=None, max_length=500, description="진행 상태 변경 사유")


class Resource(ProjectModel):
    pass


class OwnerData(Resource):
    user_id: int
    nickname: str


class TopicData(Resource):
    topic_id: int
    topic_code: str
    topic_name: str
    is_active: bool


class TechStackData(Resource):
    tech_stack_id: int
    tech_stack_code: str
    tech_stack_name: str
    category: str | None = None
    is_active: bool


class RoleData(Resource):
    role_id: int
    role_code: str
    role_name: str
    is_active: bool


class PositionData(Resource):
    project_position_id: int
    position_title: str
    required_count: int
    accepted_count: int = 0
    position_status: str
    role: RoleData
    responsibilities: str | None = None
    required_level: str | None = None


class ProjectCard(Resource):
    project_id: int
    title: str
    summary: str
    work_type: str
    region: str | None
    recruitment_deadline: datetime
    recruitment_status: str
    project_status: str
    view_count: int
    created_at: datetime
    owner: OwnerData
    topics: list[TopicData]
    tech_stacks: list[TechStackData]
    positions: list[PositionData]
    is_applied: bool | None = None
    is_bookmarked: bool | None = None


class MemberSummary(Resource):
    total_members: int


class ProjectDetailData(Resource):
    project: ProjectCard
    description: str
    expected_start_date: date | None
    expected_end_date: date | None
    weekly_hours: int | None
    visibility: str
    updated_at: datetime
    share_url: str
    owner_profile: dict
    member_summary: MemberSummary
    my_application: dict | None = None
    collaboration_channels: list[dict] | None = None


class PageMeta(Resource):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class ProjectPageData(Resource):
    items: list[ProjectCard]


class ProjectPageResponse(Resource):
    success: bool = True
    data: ProjectPageData
    meta: PageMeta
    request_id: str


class ProjectDetailResponse(Resource):
    success: bool = True
    data: ProjectDetailData
    request_id: str


class ProjectStatusData(Resource):
    project_id: int
    project_status: str
    recruitment_status: str
    updated_at: datetime


class ProjectStatusResponse(Resource):
    success: bool = True
    data: ProjectStatusData
    request_id: str


def _unique(values: list[int], name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{name}에 중복 항목을 포함할 수 없습니다.")
