"""프로젝트 팀원 도메인 예외."""

from app.core.exceptions import AppException


class MemberNotFoundError(AppException):
    def __init__(self, member_id: int | None = None) -> None:
        super().__init__(
            status_code=404,
            code="MEMBER_NOT_FOUND",
            message="팀원을 찾을 수 없습니다.",
            details={"member_id": member_id} if member_id else None,
        )


class MemberAccessDeniedError(AppException):
    def __init__(self) -> None:
        super().__init__(status_code=403, code="ACCESS_DENIED", message="접근 권한이 없습니다.")


class MemberInvalidStateTransitionError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message="현재 상태에서는 요청을 처리할 수 없습니다.",
        )


class MemberPositionCapacityExceededError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            code="POSITION_CAPACITY_EXCEEDED",
            message="모집 정원이 모두 찼습니다.",
        )
