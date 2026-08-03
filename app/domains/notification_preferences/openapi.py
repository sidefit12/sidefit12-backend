"""사용자 알림 수신 설정 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

UPDATE_EXAMPLE = {
    "applicationEnabled": True,
    "recruitmentDeadlineEnabled": True,
    "teamEnabled": False,
    "systemEnabled": True,
}
PREFERENCE_EXAMPLE = {
    "success": True,
    "data": {
        "applicationEnabled": True,
        "recruitmentDeadlineEnabled": True,
        "teamEnabled": False,
        "systemEnabled": True,
        "updatedAt": "2026-08-02T05:00:00Z",
    },
    "requestId": "req_01HXYZ",
}


def response_example(description: str, example: dict) -> dict:
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(description: str, code: str, message: str) -> dict:
    return {
        "description": description,
        "content": {
            "application/json": {"example": {"code": code, "message": message, "details": None}}
        },
    }


def apply_notification_preference_openapi(schema: dict) -> dict:
    """알림 설정 API의 요청·성공 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={"NOTI_005", "NOTI_006"},
        request_examples={"NOTI_006": UPDATE_EXAMPLE},
        success_examples={
            "NOTI_005": PREFERENCE_EXAMPLE,
            "NOTI_006": PREFERENCE_EXAMPLE,
        },
    )
