"""프로젝트 북마크 API의 Swagger 응답 예시."""

from app.core.openapi import apply_examples
from app.domains.projects.openapi import PAGE_EXAMPLE

BOOKMARKED_EXAMPLE = {
    "success": True,
    "data": {"projectId": 100, "bookmarked": True},
    "requestId": "req_01HXYZ",
}
UNBOOKMARKED_EXAMPLE = {
    "success": True,
    "data": {"projectId": 100, "bookmarked": False},
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


def apply_bookmark_openapi(schema: dict) -> dict:
    """북마크 API의 성공 응답 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={"BOOKMARK_001", "BOOKMARK_002", "BOOKMARK_003"},
        request_examples={},
        success_examples={
            "BOOKMARK_001": BOOKMARKED_EXAMPLE,
            "BOOKMARK_002": UNBOOKMARKED_EXAMPLE,
            "BOOKMARK_003": PAGE_EXAMPLE,
        },
    )
