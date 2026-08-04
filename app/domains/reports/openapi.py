"""신고와 관리자 API Swagger 예시."""

from app.core.openapi import apply_examples

REQUEST = {"reasonType": "MISLEADING_INFORMATION", "detail": "모집 내용과 실제 안내가 다릅니다."}
REPORT = {
    "reportId": 600,
    "targetType": "PROJECT",
    "targetUserId": None,
    "targetProjectId": 100,
    "reasonType": "MISLEADING_INFORMATION",
    "detail": "설명과 실제가 다릅니다.",
    "reportStatus": "PENDING",
    "resolutionNote": None,
    "createdAt": "2026-08-02T05:00:00Z",
}
ONE = {"success": True, "data": REPORT, "requestId": "req_01HXYZ"}
PAGE = {
    "success": True,
    "data": {"items": [REPORT]},
    "meta": {"page": 0, "size": 20, "totalElements": 1, "totalPages": 1, "hasNext": False},
    "requestId": "req_01HXYZ",
}
DETAIL = {
    "success": True,
    "data": {
        "report": REPORT,
        "reporter": {
            "userId": 1,
            "nickname": "reporter",
            "userStatus": "ACTIVE",
            "systemRole": "USER",
            "onboardingCompleted": True,
        },
        "target": {"projectId": 100, "title": "프로젝트"},
        "handledBy": None,
        "handledAt": None,
    },
    "requestId": "req_01HXYZ",
}
PROCESS = {
    "reportStatus": "RESOLVED",
    "resolutionNote": "검토 결과 모집글을 숨김 처리했습니다.",
    "action": "HIDE_PROJECT",
}


def response_example(description, example):
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(description, code, message):
    return response_example(description, {"code": code, "message": message, "details": None})


def apply_report_openapi(schema):
    return apply_examples(
        schema,
        operation_ids={"REPORT_001", "REPORT_002", "ADMIN_001", "ADMIN_002", "ADMIN_003"},
        request_examples={"REPORT_001": REQUEST, "REPORT_002": REQUEST, "ADMIN_003": PROCESS},
        success_examples={
            "REPORT_001": ONE,
            "REPORT_002": ONE,
            "ADMIN_001": PAGE,
            "ADMIN_002": DETAIL,
            "ADMIN_003": DETAIL,
        },
    )
