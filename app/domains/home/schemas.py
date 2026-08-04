"""홈 화면 응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel
from app.domains.projects.schemas import ProjectCard
from app.domains.recommendations.schemas import RecommendationItem


class HomeModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ProfileSummary(HomeModel):
    user_id: int
    nickname: str
    onboarding_completed: bool
    preferred_work_type: str | None = None


class ActivitySummary(HomeModel):
    authored_project_count: int = Field(description="작성한 프로젝트 수")
    application_count: int = Field(description="전체 지원 수")
    pending_application_count: int = Field(description="검토 대기 지원 수")
    accepted_application_count: int = Field(description="승인된 지원 수")
    bookmarked_project_count: int = Field(description="북마크한 프로젝트 수")


class PartialError(HomeModel):
    section: str
    code: str
    message: str


class HomeData(HomeModel):
    profile_summary: ProfileSummary
    activity_summary: ActivitySummary
    recommendations: list[RecommendationItem]
    latest_projects: list[ProjectCard]
    closing_soon_projects: list[ProjectCard]
    partial_errors: list[PartialError]


class HomeResponse(HomeModel):
    success: bool = True
    data: HomeData
    request_id: str | None = None
