"""사용자 알림 수신 설정 API 엔드포인트."""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.notification_preferences.openapi import (
    PREFERENCE_EXAMPLE,
    UPDATE_EXAMPLE,
    error_example,
    response_example,
)
from app.domains.notification_preferences.schemas import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)
from app.domains.notification_preferences.service import NotificationPreferenceService
from app.domains.users.models import User

router = APIRouter(tags=["알림 설정"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")


def _request_id():
    return request_id_context.get()


@router.get(
    "/users/me/notification-preferences",
    response_model=NotificationPreferenceResponse,
    summary="알림 설정 조회",
    description="지원·모집 마감·팀·필수 시스템 알림의 수신 설정을 조회합니다.",
    operation_id="NOTI_005",
    responses={200: response_example("알림 설정 조회 성공", PREFERENCE_EXAMPLE), 401: AUTH},
)
def get_notification_preferences(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    data = NotificationPreferenceService.get(db, user)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/users/me/notification-preferences",
    response_model=NotificationPreferenceResponse,
    summary="알림 설정 수정",
    description="알림 유형별 수신 여부를 부분 수정하며 필수 시스템 알림은 비활성화할 수 없습니다.",
    operation_id="NOTI_006",
    responses={
        200: response_example("알림 설정 수정 성공", PREFERENCE_EXAMPLE),
        400: error_example("잘못된 설정", "VALIDATION_ERROR", "입력값을 확인해 주세요."),
        401: AUTH,
    },
)
def update_notification_preferences(
    request: NotificationPreferenceUpdateRequest = Body(
        openapi_examples={"default": {"summary": "알림 설정 수정 예시", "value": UPDATE_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = NotificationPreferenceService.update(db, user, request)
    return {"success": True, "data": data, "requestId": _request_id()}
