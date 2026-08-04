"""프로젝트 협업 채널 예외."""

from app.core.exceptions import AppException


class ChannelNotFoundError(AppException):
    def __init__(self):
        super().__init__(
            status_code=404, code="CHANNEL_NOT_FOUND", message="협업 채널을 찾을 수 없습니다."
        )


class ChannelAccessDeniedError(AppException):
    def __init__(self):
        super().__init__(status_code=403, code="ACCESS_DENIED", message="접근 권한이 없습니다.")
