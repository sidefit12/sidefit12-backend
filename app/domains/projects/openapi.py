"""프로젝트 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

CREATE_EXAMPLE = {
    "title": "AI 기반 자산관리 프로젝트",
    "summary": "개인화 자산관리 웹 서비스를 함께 만듭니다.",
    "description": "프로젝트 목표와 진행 방식을 설명합니다.",
    "workType": "ONLINE",
    "region": "서울 강남",
    "expectedStartDate": "2026-09-01",
    "expectedEndDate": "2026-12-31",
    "weeklyHours": 10,
    "recruitmentDeadline": "2026-08-31T14:59:59Z",
    "visibility": "PUBLIC",
    "topicIds": [1, 3],
    "techStacks": [{"techStackId": 4, "requirementType": "REQUIRED", "requiredLevel": "BEGINNER"}],
    "positions": [
        {
            "roleId": 2,
            "positionTitle": "백엔드 개발자",
            "responsibilities": "API와 DB 설계",
            "requiredCount": 2,
            "requiredLevel": "BEGINNER",
        }
    ],
}
UPDATE_EXAMPLE = {
    "title": "AI 기반 자산관리 프로젝트 개선",
    "summary": "개인화 자산관리 서비스의 모집 조건을 변경합니다.",
    "weeklyHours": 12,
    "topicIds": [1, 3],
}
CARD_EXAMPLE = {
    "projectId": 100,
    "title": "AI 기반 자산관리 프로젝트",
    "summary": "개인화 자산관리 웹 서비스를 함께 만듭니다.",
    "workType": "ONLINE",
    "region": "서울",
    "recruitmentDeadline": "2026-08-31T14:59:59Z",
    "recruitmentStatus": "RECRUITING",
    "projectStatus": "PREPARING",
    "viewCount": 120,
    "createdAt": "2026-08-01T10:00:00Z",
    "owner": {"userId": 1, "nickname": "leader"},
    "topics": [{"topicId": 1, "topicCode": "FINTECH", "topicName": "핀테크", "isActive": True}],
    "techStacks": [
        {
            "techStackId": 4,
            "techStackCode": "FASTAPI",
            "techStackName": "FastAPI",
            "category": "Backend",
            "isActive": True,
        }
    ],
    "positions": [
        {
            "projectPositionId": 21,
            "positionTitle": "백엔드 개발자",
            "requiredCount": 2,
            "acceptedCount": 1,
            "positionStatus": "OPEN",
            "role": {"roleId": 2, "roleCode": "BACKEND", "roleName": "백엔드", "isActive": True},
        }
    ],
    "isApplied": False,
    "isBookmarked": True,
}
PAGE_EXAMPLE = {
    "success": True,
    "data": {"items": [CARD_EXAMPLE]},
    "meta": {"page": 0, "size": 20, "totalElements": 1, "totalPages": 1, "hasNext": False},
    "requestId": "req_01HXYZ",
}
DETAIL_EXAMPLE = {
    "success": True,
    "data": {
        "project": CARD_EXAMPLE,
        "description": "프로젝트 목표와 진행 방식을 설명합니다.",
        "expectedStartDate": "2026-09-01",
        "expectedEndDate": "2026-12-31",
        "weeklyHours": 10,
        "visibility": "PUBLIC",
        "updatedAt": "2026-08-02T05:00:00Z",
        "shareUrl": "https://sidefit.dev/projects/100",
        "ownerProfile": {"userId": 1, "nickname": "leader"},
        "memberSummary": {"totalMembers": 1},
        "myApplication": None,
        "collaborationChannels": None,
    },
    "requestId": "req_01HXYZ",
}
STATUS_EXAMPLE = {
    "success": True,
    "data": {
        "projectId": 100,
        "projectStatus": "PREPARING",
        "recruitmentStatus": "CLOSED",
        "updatedAt": "2026-08-02T05:00:00Z",
    },
    "requestId": "req_01HXYZ",
}


def response_example(description: str, example: dict) -> dict:
    """Swagger 성공 응답 설명과 예시를 생성한다."""
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(description: str, code: str, message: str) -> dict:
    """Swagger 오류 응답 설명과 예시를 생성한다."""
    return response_example(
        description, {"code": code, "message": message, "details": None, "requestId": "req_01HXYZ"}
    )


OPERATION_IDS = {
    "PROJECT_001_list",
    "PROJECT_002_create",
    "PROJECT_003_detail",
    "PROJECT_004_update",
    "PROJECT_005_delete",
    "PROJECT_006_recruitment_status",
    "PROJECT_007_status",
    "PROJECT_009_my_projects",
}


def apply_project_openapi(schema: dict) -> dict:
    """프로젝트 API의 자동 생성 오류 응답 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids=OPERATION_IDS,
        request_examples={},
        success_examples={},
    )
