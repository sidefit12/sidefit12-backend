"""도메인별 Swagger 예시를 OpenAPI 문서에 적용하는 공통 도구."""


def apply_examples(
    schema: dict,
    *,
    operation_ids: set[str],
    request_examples: dict[str, dict],
    success_examples: dict[str, dict],
) -> dict:
    """지정한 도메인의 요청·성공·오류 예시를 operationId 기준으로 등록한다."""
    for methods in schema.get("paths", {}).values():
        for operation in methods.values():
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if operation_id not in operation_ids:
                continue
            if operation_id in request_examples:
                media = operation["requestBody"]["content"]["application/json"]
                media["examples"] = {
                    "default": {
                        "summary": "요청 예시",
                        "value": request_examples[operation_id],
                    }
                }
            if operation_id in success_examples:
                for code, response in operation.get("responses", {}).items():
                    if code.startswith("2"):
                        media = response.setdefault("content", {}).setdefault(
                            "application/json", {}
                        )
                        media["example"] = {
                            **success_examples[operation_id],
                            "requestId": "req_01HXYZ",
                        }
            for code, response in operation.get("responses", {}).items():
                if code.startswith(("4", "5")):
                    media = response.setdefault("content", {}).setdefault("application/json", {})
                    media.setdefault(
                        "example",
                        {
                            "code": "VALIDATION_ERROR",
                            "message": response.get("description", "요청을 처리할 수 없습니다."),
                            "details": None,
                            "requestId": "req_01HXYZ",
                        },
                    )
    return schema
