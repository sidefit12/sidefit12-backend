"""기준정보 API에서 사용하는 도메인 예외."""

from fastapi import status

from app.core.exceptions import AppException


class ReferenceDataAdminRequiredError(AppException):
    """비활성 기준정보 조회에 관리자 권한이 없을 때 발생한다."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ADMIN_PERMISSION_REQUIRED",
            message="비활성 기준정보 조회에는 관리자 권한이 필요합니다.",
        )
