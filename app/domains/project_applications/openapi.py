"""프로젝트 지원 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

CREATE_REQUEST_EXAMPLE = {
    "applicationMessage": "백엔드 API 개발 경험으로 프로젝트에 기여하겠습니다.",
    "projectPositionId": 21,
}
CANCEL_REQUEST_EXAMPLE = {"reason": "일정이 맞지 않아 지원을 취소합니다."}
ACCEPT_REQUEST_EXAMPLE = {"note": "합류를 환영합니다."}
REJECT_REQUEST_EXAMPLE = {
    "rejectionReasonCode": "ROLE_MISMATCH",
    "rejectionReason": "현재 포지션 요구 경험과 차이가 있습니다.",
}
APPLICATION_EXAMPLE = {
    "applicationId": 200,
    "projectId": 100,
    "projectTitle": "사이드 프로젝트 팀원 모집",
    "projectPositionId": 21,
    "applicationMessage": "백엔드 API 개발 경험으로 프로젝트에 기여하겠습니다.",
    "applicationStatus": "PENDING",
    "appliedAt": "2026-08-02T05:00:00Z",
    "reviewedAt": None,
    "rejectionReason": None,
    "applicant": {"userId": 2, "nickname": "applicant"},
}
APPLICATION_RESPONSE_EXAMPLE = {
    "success": True,
    "data": APPLICATION_EXAMPLE,
    "requestId": "req_01HXYZ",
}
PAGE_RESPONSE_EXAMPLE = {
    "success": True,
    "data": {"items": [APPLICATION_EXAMPLE], "statusCounts": {"PENDING": 1}},
    "meta": {
        "page": 0,
        "size": 20,
        "totalElements": 1,
        "totalPages": 1,
        "hasNext": False,
    },
    "requestId": "req_01HXYZ",
}
DETAIL_RESPONSE_EXAMPLE = {
    "success": True,
    "data": {
        "application": APPLICATION_EXAMPLE,
        "applicantProfile": {
            "userId": 2,
            "nickname": "applicant",
            "introduction": "백엔드 개발자입니다.",
            "profileImageFileId": None,
            "publicMaterialFileId": None,
            "externalLinkUrl": None,
            "topics": [],
            "techStacks": [],
            "roles": [],
        },
        "submittedSnapshot": None,
    },
    "requestId": "req_01HXYZ",
}
DECISION_RESPONSE_EXAMPLE = {
    "success": True,
    "data": {
        "application": {**APPLICATION_EXAMPLE, "applicationStatus": "ACCEPTED"},
        "member": {
            "projectMemberId": 300,
            "projectId": 100,
            "projectPositionId": 21,
            "memberType": "MEMBER",
            "memberStatus": "ACTIVE",
            "joinedAt": "2026-08-03T05:00:00Z",
            "leftAt": None,
            "user": {
                "userId": 2,
                "nickname": "applicant",
                "userStatus": "ACTIVE",
                "systemRole": "USER",
                "onboardingCompleted": True,
                "profileImageUrl": None,
                "email": None,
            },
        },
        "positionSummary": {"requiredCount": 2, "acceptedCount": 1, "positionStatus": "OPEN"},
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


def apply_application_openapi(schema: dict) -> dict:
    """지원 API의 요청·성공 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={f"APP_00{i}" for i in range(1, 8)},
        request_examples={
            "APP_001": CREATE_REQUEST_EXAMPLE,
            "APP_003": CANCEL_REQUEST_EXAMPLE,
            "APP_006": ACCEPT_REQUEST_EXAMPLE,
            "APP_007": REJECT_REQUEST_EXAMPLE,
        },
        success_examples={
            "APP_001": APPLICATION_RESPONSE_EXAMPLE,
            "APP_002": PAGE_RESPONSE_EXAMPLE,
            "APP_003": APPLICATION_RESPONSE_EXAMPLE,
            "APP_004": PAGE_RESPONSE_EXAMPLE,
            "APP_005": DETAIL_RESPONSE_EXAMPLE,
            "APP_006": DECISION_RESPONSE_EXAMPLE,
            "APP_007": DECISION_RESPONSE_EXAMPLE,
        },
    )
