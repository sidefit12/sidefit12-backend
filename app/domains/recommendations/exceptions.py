"""추천 API 예외."""

from app.core.exceptions import AppException


class InvalidRecommendationCursorError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=400, code="INVALID_CURSOR", message="추천 커서가 올바르지 않습니다."
        )


class RecommendationUnavailableError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=503,
            code="RECOMMENDATION_UNAVAILABLE",
            message="추천 서비스를 일시적으로 사용할 수 없습니다.",
        )
