"""사용자 알림 조회와 읽음 처리 API 엔드포인트."""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.notifications.openapi import (
    PAGE_EXAMPLE,
    READ_ALL_EXAMPLE,
    READ_ALL_REQUEST_EXAMPLE,
    READ_EXAMPLE,
    UNREAD_EXAMPLE,
    error_example,
    response_example,
)
from app.domains.notifications.schemas import (
    NotificationPageResponse,
    NotificationResponse,
    ReadAllNotificationsRequest,
    ReadAllNotificationsResponse,
    UnreadCountResponse,
)
from app.domains.notifications.service import NotificationService
from app.domains.users.models import User

router = APIRouter(tags=["알림"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")
NotificationType = Literal[
    "APPLICATION_RECEIVED",
    "APPLICATION_ACCEPTED",
    "APPLICATION_REJECTED",
    "RECRUITMENT_CLOSED",
    "MEMBER_JOINED",
    "MEMBER_LEFT",
    "PROJECT_STATUS_CHANGED",
    "SYSTEM",
]


def _request_id():
    return request_id_context.get()


@router.get(
    "/notifications",
    response_model=NotificationPageResponse,
    summary="알림 목록 조회",
    description="현재 사용자의 알림 목록과 전체 미읽음 개수를 최신순으로 반환합니다.",
    operation_id="NOTI_001",
    responses={200: response_example("알림 목록 조회 성공", PAGE_EXAMPLE), 401: AUTH},
)
def list_notifications(
    is_read: bool | None = Query(None, alias="isRead", description="알림 읽음 여부 필터"),
    notification_type: NotificationType | None = Query(
        None, alias="notificationType", description="확정된 알림 유형 필터"
    ),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = NotificationService.page(
        db,
        user,
        page=page,
        size=size,
        is_read=is_read,
        notification_type=notification_type,
    )
    return {"success": True, "data": data, "meta": meta, "requestId": _request_id()}


@router.get(
    "/notifications/unread-count",
    response_model=UnreadCountResponse,
    summary="미읽음 알림 수 조회",
    description="헤더 배지에 표시할 현재 사용자의 미읽음 알림 수를 반환합니다.",
    operation_id="NOTI_002",
    responses={200: response_example("미읽음 알림 수 조회 성공", UNREAD_EXAMPLE), 401: AUTH},
)
def get_unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "success": True,
        "data": {"unreadCount": NotificationService.unread_count(db, user)},
        "requestId": _request_id(),
    }


@router.patch(
    "/notifications/{notificationId}/read",
    response_model=NotificationResponse,
    summary="알림 읽음 처리",
    description="본인의 알림에 읽음 시각을 멱등하게 기록합니다.",
    operation_id="NOTI_003",
    responses={
        200: response_example("알림 읽음 처리 성공", READ_EXAMPLE),
        401: AUTH,
        403: error_example("접근 권한 없음", "ACCESS_DENIED", "접근 권한이 없습니다."),
        404: error_example("알림 없음", "NOTIFICATION_NOT_FOUND", "알림을 찾을 수 없습니다."),
    },
)
def read_notification(
    notification_id: int = Path(alias="notificationId", gt=0, description="알림 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = NotificationService.read(db, user, notification_id)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/notifications/read-all",
    response_model=ReadAllNotificationsResponse,
    summary="알림 전체 읽음 처리",
    description="기준 시각 이전에 생성된 현재 사용자의 미읽음 알림을 일괄 처리합니다.",
    operation_id="NOTI_004",
    responses={
        200: response_example("알림 전체 읽음 처리 성공", READ_ALL_EXAMPLE),
        401: AUTH,
    },
)
def read_all_notifications(
    request: ReadAllNotificationsRequest | None = Body(
        None,
        openapi_examples={
            "default": {"summary": "전체 읽음 요청 예시", "value": READ_ALL_REQUEST_EXAMPLE}
        },
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = NotificationService.read_all(db, user, request.before if request else None)
    return {"success": True, "data": data, "requestId": _request_id()}
