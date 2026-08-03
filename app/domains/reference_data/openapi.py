"""기준정보 API의 Swagger 응답 예시."""

from app.core.openapi import apply_examples

TOPICS_EXAMPLE = {
    "success": True,
    "data": {
        "items": [{"topicId": 1, "topicCode": "FINTECH", "topicName": "핀테크", "isActive": True}]
    },
    "requestId": "req_01HXYZ",
}
TECH_STACKS_EXAMPLE = {
    "success": True,
    "data": {
        "items": [
            {
                "techStackId": 1,
                "techStackCode": "JAVA",
                "techStackName": "Java",
                "category": "언어",
                "isActive": True,
            }
        ]
    },
    "requestId": "req_01HXYZ",
}
ROLES_EXAMPLE = {
    "success": True,
    "data": {
        "items": [
            {
                "roleId": 1,
                "roleCode": "BACKEND",
                "roleName": "백엔드 개발자",
                "isActive": True,
            }
        ]
    },
    "requestId": "req_01HXYZ",
}


def response_example(description: str, example: dict) -> dict:
    """성공 응답 설명과 예시를 반환한다."""
    return {"description": description, "content": {"application/json": {"example": example}}}


def error_example(description: str, code: str, message: str) -> dict:
    """공통 오류 응답의 설명과 예시를 반환한다."""
    return {
        "description": description,
        "content": {
            "application/json": {"example": {"code": code, "message": message, "details": None}}
        },
    }


def apply_reference_data_openapi(schema: dict) -> dict:
    """기준정보 API의 성공 응답 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids={
            "MASTER_001_list_topics",
            "MASTER_002_list_tech_stacks",
            "MASTER_003_list_roles",
        },
        request_examples={},
        success_examples={
            "MASTER_001_list_topics": TOPICS_EXAMPLE,
            "MASTER_002_list_tech_stacks": TECH_STACKS_EXAMPLE,
            "MASTER_003_list_roles": ROLES_EXAMPLE,
        },
    )
