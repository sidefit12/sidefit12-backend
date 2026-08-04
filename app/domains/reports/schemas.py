"""신고 요청 및 응답 스키마."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel
from app.domains.projects.schemas import PageMeta

ReasonType = Literal[
    "SPAM", "HARASSMENT", "MISLEADING_INFORMATION", "INAPPROPRIATE_CONTENT", "OTHER"
]
ReportStatus = Literal["PENDING", "IN_REVIEW", "RESOLVED", "REJECTED"]


class ReportModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ReportCreateRequest(ReportModel):
    reason_type: ReasonType = Field(description="신고 사유", examples=["MISLEADING_INFORMATION"])
    detail: str | None = Field(None, max_length=2000, description="신고 상세 내용")


class ReportResource(ReportModel):
    report_id: int
    target_type: Literal["USER", "PROJECT"]
    target_user_id: int | None = None
    target_project_id: int | None = None
    reason_type: str
    detail: str | None
    report_status: str
    resolution_note: str | None
    created_at: datetime


class ReportResponse(ReportModel):
    success: bool = True
    data: ReportResource
    request_id: str | None = None


class ReportPageData(ReportModel):
    items: list[ReportResource]


class ReportPageResponse(ReportModel):
    success: bool = True
    data: ReportPageData
    meta: PageMeta
    request_id: str | None = None


class AdminReportRequest(ReportModel):
    report_status: ReportStatus = Field(description="변경할 신고 처리 상태")
    resolution_note: str = Field(min_length=10, max_length=2000, description="관리자 처리 메모")
    action: Literal["NONE", "HIDE_PROJECT", "SUSPEND_USER"] | None = Field(
        None, description="신고 대상 조치"
    )


class AdminUserSummary(ReportModel):
    user_id: int
    nickname: str
    user_status: str
    system_role: str
    onboarding_completed: bool
    profile_image_url: str | None = None
    email: str | None = None


class AdminReportDetail(ReportModel):
    report: ReportResource
    reporter: AdminUserSummary
    target: dict
    handled_by: AdminUserSummary | None = None
    handled_at: datetime | None = None


class AdminReportDetailResponse(ReportModel):
    success: bool = True
    data: AdminReportDetail
    request_id: str | None = None
