"""파일 API Swagger 예시."""

from app.core.openapi import apply_examples

FILE_EXAMPLE = {
    "success": True,
    "data": {
        "file": {
            "fileId": 10,
            "originalName": "portfolio.pdf",
            "mimeType": "application/pdf",
            "fileSize": 102400,
            "fileCategory": "PUBLIC_MATERIAL",
            "visibility": "PUBLIC",
            "previewAllowed": True,
            "downloadAllowed": True,
            "url": "https://cdn.example/file",
            "createdAt": "2026-08-02T05:00:00Z",
        }
    },
    "requestId": "req_01HXYZ",
}


def response_example(description: str, example: dict | None = None) -> dict:
    result = {"description": description}
    if example is not None:
        result["content"] = {"application/json": {"example": example}}
    return result


def error_example(description: str, code: str, message: str) -> dict:
    return {
        "description": description,
        "content": {
            "application/json": {"example": {"code": code, "message": message, "details": None}}
        },
    }


def apply_file_openapi(schema: dict) -> dict:
    """파일 API 성공 응답 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={"FILE_001", "FILE_002"},
        request_examples={},
        success_examples={"FILE_001": FILE_EXAMPLE},
    )
