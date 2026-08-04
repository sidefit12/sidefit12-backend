"""홈 API Swagger 예시."""

from app.core.openapi import apply_examples

HOME_EXAMPLE = {
    "success": True,
    "data": {
        "profileSummary": {
            "userId": 1,
            "nickname": "sidefitter",
            "onboardingCompleted": True,
            "preferredWorkType": "ONLINE",
        },
        "activitySummary": {
            "authoredProjectCount": 1,
            "applicationCount": 2,
            "pendingApplicationCount": 1,
            "acceptedApplicationCount": 1,
            "bookmarkedProjectCount": 3,
        },
        "recommendations": [],
        "latestProjects": [],
        "closingSoonProjects": [],
        "partialErrors": [],
    },
}


def apply_home_openapi(schema: dict) -> dict:
    """홈 API 응답 예시를 적용한다."""
    return apply_examples(
        schema,
        operation_ids={"HOME_001"},
        request_examples={},
        success_examples={"HOME_001": HOME_EXAMPLE},
    )
