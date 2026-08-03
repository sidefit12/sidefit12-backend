"""사용자 알림 도메인 예외."""

from app.core.exceptions import AppException


class NotificationNotFoundError(AppException):
    def __init__(self, notification_id: int) -> None:
        super().__init__(
            status_code=404,
            code="NOTIFICATION_NOT_FOUND",
            message="알림을 찾을 수 없습니다.",
            details={"notification_id": notification_id},
        )


class NotificationAccessDeniedError(AppException):
    def __init__(self) -> None:
        super().__init__(status_code=403, code="ACCESS_DENIED", message="접근 권한이 없습니다.")
