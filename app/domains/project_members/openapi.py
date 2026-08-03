"""프로젝트 팀원 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

LEAVE_EXAMPLE = {"reason": "개인 일정으로 참여가 어렵습니다."}
REMOVE_EXAMPLE = {"reason": "지속적인 무단 불참으로 팀에서 제외합니다."}
RESTORE_EXAMPLE = {"reason": "일정 협의 후 프로젝트 팀원으로 복구합니다."}
USER_EXAMPLE = {
    "userId": 2,
    "nickname": "sidefitter",
    "userStatus": "ACTIVE",
    "systemRole": "USER",
    "onboardingCompleted": True,
    "profileImageUrl": None,
    "email": None,
}
MEMBER_EXAMPLE = {
    "projectMemberId": 300,
    "projectId": 100,
    "projectPositionId": 21,
    "memberType": "MEMBER",
    "memberStatus": "ACTIVE",
    "joinedAt": "2026-08-03T05:00:00Z",
    "leftAt": None,
    "user": USER_EXAMPLE,
}
LIST_EXAMPLE = {
    "success": True,
    "data": {
        "items": [MEMBER_EXAMPLE],
        "positionSummary": {
            "21": {
                "projectPositionId": 21,
                "positionTitle": "백엔드 개발자",
                "requiredCount": 2,
                "activeCount": 1,
                "positionStatus": "OPEN",
            }
        },
        "channels": None,
    },
    "requestId": "req_01HXYZ",
}
MEMBER_RESPONSE_EXAMPLE = {
    "success": True,
    "data": {"member": MEMBER_EXAMPLE},
    "requestId": "req_01HXYZ",
}
EVENT_PAGE_EXAMPLE = {
    "success": True,
    "data": {
        "items": [
            {
                "eventType": "REMOVED",
                "reason": "지속적인 무단 불참으로 팀에서 제외합니다.",
                "createdAt": "2026-08-03T05:00:00Z",
                "actor": USER_EXAMPLE,
            }
        ]
    },
    "meta": {
        "page": 0,
        "size": 20,
        "totalElements": 1,
        "totalPages": 1,
        "hasNext": False,
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


def apply_member_openapi(schema: dict) -> dict:
    """팀원 API의 요청·성공 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={f"MEMBER_00{i}" for i in range(1, 6)},
        request_examples={
            "MEMBER_002": LEAVE_EXAMPLE,
            "MEMBER_003": REMOVE_EXAMPLE,
            "MEMBER_004": RESTORE_EXAMPLE,
        },
        success_examples={
            "MEMBER_001": LIST_EXAMPLE,
            "MEMBER_002": MEMBER_RESPONSE_EXAMPLE,
            "MEMBER_003": MEMBER_RESPONSE_EXAMPLE,
            "MEMBER_004": MEMBER_RESPONSE_EXAMPLE,
            "MEMBER_005": EVENT_PAGE_EXAMPLE,
        },
    )
