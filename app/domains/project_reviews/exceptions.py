"""프로젝트 리뷰 예외."""

from app.core.exceptions import AppException


class ReviewNotFoundError(AppException):
    def __init__(self):
        super().__init__(
            status_code=404, code="REVIEW_NOT_FOUND", message="리뷰를 찾을 수 없습니다."
        )


class ReviewAlreadyExistsError(AppException):
    def __init__(self):
        super().__init__(
            status_code=409, code="REVIEW_ALREADY_EXISTS", message="이미 리뷰를 작성했습니다."
        )


class ReviewAccessDeniedError(AppException):
    def __init__(self):
        super().__init__(status_code=403, code="ACCESS_DENIED", message="접근 권한이 없습니다.")


class ReviewOwnershipRequiredError(AppException):
    def __init__(self):
        super().__init__(
            status_code=403,
            code="RESOURCE_OWNERSHIP_REQUIRED",
            message="리소스 소유자만 처리할 수 있습니다.",
        )


class ReviewInvalidStateError(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message="현재 상태에서는 요청을 처리할 수 없습니다.",
        )
