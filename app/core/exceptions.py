"""애플리케이션 공통 예외를 정의하는 모듈."""

from typing import Any


class AppException(Exception):
    """전역 예외 처리 대상이 되는 애플리케이션 기본 예외."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

        super().__init__(message)
