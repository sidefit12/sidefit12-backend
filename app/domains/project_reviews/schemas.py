"""프로젝트 리뷰 요청 및 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel
from app.domains.projects.schemas import PageMeta


class ReviewModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ReviewCreateRequest(ReviewModel):
    rating: int = Field(ge=1, le=5, description="1점부터 5점까지의 평점", examples=[5])
    content: str | None = Field(
        None, max_length=2000, description="리뷰 내용", examples=["협업 과정이 체계적이었습니다."]
    )


class ReviewUpdateRequest(ReviewModel):
    rating: int | None = Field(None, ge=1, le=5, description="변경할 평점")
    content: str | None = Field(None, max_length=2000, description="변경할 리뷰 내용")


class ReviewerSummary(ReviewModel):
    user_id: int
    nickname: str
    user_status: str
    system_role: str
    onboarding_completed: bool
    profile_image_url: str | None = None
    email: str | None = None


class ReviewResource(ReviewModel):
    review_id: int
    project_id: int
    rating: int
    content: str | None
    created_at: datetime
    reviewer: ReviewerSummary


class ReviewPageData(ReviewModel):
    average_rating: float
    review_count: int
    items: list[ReviewResource]


class ReviewResponse(ReviewModel):
    success: bool = True
    data: ReviewResource
    request_id: str | None = None


class ReviewPageResponse(ReviewModel):
    success: bool = True
    data: ReviewPageData
    meta: PageMeta
    request_id: str | None = None
