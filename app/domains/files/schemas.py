"""파일 API 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel


class FileModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class FileResource(FileModel):
    file_id: int = Field(description="파일 식별자", examples=[10])
    original_name: str = Field(description="업로드한 원본 파일명", examples=["portfolio.pdf"])
    mime_type: str = Field(description="검증된 MIME 유형", examples=["application/pdf"])
    file_size: int = Field(description="파일의 바이트 크기", examples=[102400])
    file_category: str = Field(description="파일 분류", examples=["PUBLIC_MATERIAL"])
    visibility: str = Field(description="파일 공개 범위", examples=["PUBLIC"])
    preview_allowed: bool = Field(description="미리보기 허용 여부", examples=[True])
    download_allowed: bool = Field(description="다운로드 허용 여부", examples=[True])
    url: str = Field(description="파일 접근 URL 또는 서명 URL")
    created_at: datetime = Field(description="파일 생성 일시")


class FileData(FileModel):
    file: FileResource


class FileUploadResponse(FileModel):
    success: bool = True
    data: FileData
    request_id: str | None = None
