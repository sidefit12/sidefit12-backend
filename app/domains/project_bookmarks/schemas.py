"""프로젝트 북마크 API 응답 스키마."""

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel


class BookmarkModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BookmarkStateData(BookmarkModel):
    project_id: int = Field(description="프로젝트 식별자", examples=[100])
    bookmarked: bool = Field(description="현재 북마크 상태", examples=[True])


class BookmarkStateResponse(BookmarkModel):
    success: bool = True
    data: BookmarkStateData
    request_id: str | None = None
