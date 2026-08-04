"""사용자 푸시 기기 등록·삭제 API."""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.notifications.openapi import error_example, response_example
from app.domains.push_devices.schemas import (
    PushDeviceDeleteRequest,
    PushDeviceDeleteResponse,
    PushDeviceRegisterRequest,
    PushDeviceResponse,
)
from app.domains.push_devices.service import PushDeviceService
from app.domains.users.models import User

router = APIRouter(tags=["푸시 알림"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")
REGISTER_REQUEST = {
    "registrationToken": "fcm-registration-token-from-client-1234567890",
    "platform": "WEB",
    "deviceName": "Chrome 브라우저",
}
REGISTER_RESPONSE = {
    "success": True,
    "data": {
        "pushDeviceId": 1,
        "platform": "WEB",
        "deviceName": "Chrome 브라우저",
        "isActive": True,
    },
    "requestId": "req_01HXYZ",
}
DELETE_RESPONSE = {
    "success": True,
    "data": {"deleted": True},
    "requestId": "req_01HXYZ",
}


@router.post(
    "/users/me/push-devices",
    response_model=PushDeviceResponse,
    summary="푸시 기기 등록",
    description="현재 기기의 FCM 등록 토큰을 로그인 사용자에게 등록하거나 갱신합니다.",
    operation_id="PUSH_001",
    responses={200: response_example("푸시 기기 등록 성공", REGISTER_RESPONSE), 401: AUTH},
)
def register_push_device(
    request: PushDeviceRegisterRequest = Body(
        openapi_examples={"default": {"summary": "웹 푸시 기기 등록", "value": REGISTER_REQUEST}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = PushDeviceService.register(db, user, request)
    return {"success": True, "data": data, "requestId": request_id_context.get()}


@router.delete(
    "/users/me/push-devices",
    response_model=PushDeviceDeleteResponse,
    summary="푸시 기기 삭제",
    description="로그아웃하거나 알림 권한을 해제한 기기의 FCM 등록 토큰을 비활성화합니다.",
    operation_id="PUSH_002",
    responses={200: response_example("푸시 기기 삭제 성공", DELETE_RESPONSE), 401: AUTH},
)
def delete_push_device(
    request: PushDeviceDeleteRequest = Body(
        openapi_examples={
            "default": {
                "summary": "푸시 기기 삭제",
                "value": {"registrationToken": REGISTER_REQUEST["registrationToken"]},
            }
        }
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = PushDeviceService.delete(db, user, request.registration_token)
    return {
        "success": True,
        "data": {"deleted": deleted},
        "requestId": request_id_context.get(),
    }
