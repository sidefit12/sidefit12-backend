"""사용자 알림 API 요청·응답 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.auth.schemas import to_camel


class NotificationModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ReadAllNotificationsRequest(NotificationModel):
    before: datetime | None = Field(
        default=None, description="이 시각 이전에 생성된 미읽음 알림만 처리합니다."
    )


class NotificationResource(NotificationModel):
    notification_id: int
    notification_type: str
    title: str
    content: str
    reference_type: str | None = None
    reference_id: int | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationPageData(NotificationModel):
    items: list[NotificationResource]
    unread_count: int


class PageMeta(NotificationModel):
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool


class NotificationPageResponse(NotificationModel):
    success: bool = True
    data: NotificationPageData
    meta: PageMeta
    request_id: str | None = None


class UnreadCountData(NotificationModel):
    unread_count: int


class UnreadCountResponse(NotificationModel):
    success: bool = True
    data: UnreadCountData
    request_id: str | None = None


class NotificationResponse(NotificationModel):
    success: bool = True
    data: NotificationResource
    request_id: str | None = None


class ReadAllNotificationsData(NotificationModel):
    unread_count: int
    updated_count: int


class ReadAllNotificationsResponse(NotificationModel):
    success: bool = True
    data: ReadAllNotificationsData
    request_id: str | None = None
