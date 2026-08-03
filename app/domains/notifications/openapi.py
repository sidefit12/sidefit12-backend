"""사용자 알림 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

READ_ALL_REQUEST_EXAMPLE = {"before": "2026-08-02T05:00:00Z"}
NOTIFICATION_EXAMPLE = {
    "notificationId": 400,
    "notificationType": "APPLICATION_ACCEPTED",
    "title": "지원이 승인되었습니다.",
    "content": "프로젝트 팀원으로 합류했습니다.",
    "referenceType": "APPLICATION",
    "referenceId": 200,
    "isRead": False,
    "readAt": None,
    "createdAt": "2026-08-02T05:00:00Z",
}
PAGE_EXAMPLE = {
    "success": True,
    "data": {"items": [NOTIFICATION_EXAMPLE], "unreadCount": 1},
    "meta": {
        "page": 0,
        "size": 20,
        "totalElements": 1,
        "totalPages": 1,
        "hasNext": False,
    },
    "requestId": "req_01HXYZ",
}
UNREAD_EXAMPLE = {
    "success": True,
    "data": {"unreadCount": 4},
    "requestId": "req_01HXYZ",
}
READ_EXAMPLE = {
    "success": True,
    "data": {**NOTIFICATION_EXAMPLE, "isRead": True, "readAt": "2026-08-03T05:00:00Z"},
    "requestId": "req_01HXYZ",
}
READ_ALL_EXAMPLE = {
    "success": True,
    "data": {"unreadCount": 0, "updatedCount": 12},
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


def apply_notification_openapi(schema: dict) -> dict:
    """알림 API의 요청·성공 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={"NOTI_001", "NOTI_002", "NOTI_003", "NOTI_004"},
        request_examples={"NOTI_004": READ_ALL_REQUEST_EXAMPLE},
        success_examples={
            "NOTI_001": PAGE_EXAMPLE,
            "NOTI_002": UNREAD_EXAMPLE,
            "NOTI_003": READ_EXAMPLE,
            "NOTI_004": READ_ALL_EXAMPLE,
        },
    )
