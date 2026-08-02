"""사용자 도메인 예외를 정의하는 모듈."""

from app.core.exceptions import AppException


class UserNotFoundError(AppException):
    """사용자를 찾을 수 없을 때 발생하는 예외."""

    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
            details={
                "user_id": user_id,
            },
        )