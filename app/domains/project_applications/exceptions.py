"""프로젝트 지원 도메인 예외."""

from app.core.exceptions import AppException


class ApplicationNotFoundError(AppException):
    def __init__(self, application_id: int) -> None:
        super().__init__(
            status_code=404,
            code="APPLICATION_NOT_FOUND",
            message="지원 내역을 찾을 수 없습니다.",
            details={"application_id": application_id},
        )


class AlreadyAppliedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409, code="ALREADY_APPLIED", message="이미 지원한 프로젝트입니다."
        )


class RecruitmentClosedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409, code="RECRUITMENT_CLOSED", message="모집이 종료되었습니다."
        )


class PositionClosedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409, code="POSITION_CLOSED", message="해당 포지션 모집이 종료되었습니다."
        )


class CannotApplyOwnProjectError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            code="CANNOT_APPLY_OWN_PROJECT",
            message="본인이 작성한 프로젝트에는 지원할 수 없습니다.",
        )


class ApplicationAlreadyProcessedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409, code="APPLICATION_ALREADY_PROCESSED", message="이미 처리된 지원입니다."
        )


class ApplicationAccessDeniedError(AppException):
    def __init__(self) -> None:
        super().__init__(status_code=403, code="ACCESS_DENIED", message="접근 권한이 없습니다.")


class PositionCapacityExceededError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409, code="POSITION_CAPACITY_EXCEEDED", message="모집 정원이 모두 찼습니다."
        )


class ApplicationIdempotencyConflictError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            code="IDEMPOTENCY_KEY_CONFLICT",
            message="동일한 멱등 키가 다른 요청에 사용되었습니다.",
        )
