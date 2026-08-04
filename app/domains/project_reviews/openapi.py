"""프로젝트 리뷰 Swagger 예시."""

from app.core.openapi import apply_examples

REQUEST = {"rating": 5, "content": "협업 과정이 체계적이었습니다."}
REVIEW = {
    "reviewId": 801,
    "projectId": 100,
    "rating": 5,
    "content": "좋은 협업 경험이었습니다.",
    "createdAt": "2026-08-02T05:00:00Z",
    "reviewer": {
        "userId": 1,
        "nickname": "sidefitter",
        "userStatus": "ACTIVE",
        "systemRole": "USER",
        "onboardingCompleted": True,
        "profileImageUrl": None,
    },
}
ONE = {"success": True, "data": REVIEW, "requestId": "req_01HXYZ"}
PAGE = {
    "success": True,
    "data": {"averageRating": 5.0, "reviewCount": 1, "items": [REVIEW]},
    "meta": {"page": 0, "size": 20, "totalElements": 1, "totalPages": 1, "hasNext": False},
    "requestId": "req_01HXYZ",
}


def response_example(description, example):
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(description, code, message):
    return response_example(description, {"code": code, "message": message, "details": None})


def apply_review_openapi(schema):
    return apply_examples(
        schema,
        operation_ids={"REVIEW_001", "REVIEW_002", "REVIEW_003", "REVIEW_004"},
        request_examples={"REVIEW_002": REQUEST, "REVIEW_003": REQUEST},
        success_examples={"REVIEW_001": PAGE, "REVIEW_002": ONE, "REVIEW_003": ONE},
    )
