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


class ProfileNotFoundError(AppException):
    """사용자의 프로필을 찾을 수 없을 때 발생하는 예외."""

    def __init__(self, user_id: int) -> None:
        """조회하지 못한 사용자 식별자를 포함해 예외를 생성한다."""
        super().__init__(
            status_code=404,
            code="PROFILE_NOT_FOUND",
            message="프로필을 찾을 수 없습니다.",
            details={"user_id": user_id},
        )


class NicknameAlreadyExistsError(AppException):
    """이미 사용 중인 닉네임으로 프로필을 변경할 때 발생하는 예외."""

    def __init__(self, nickname: str) -> None:
        """중복 닉네임을 포함해 예외를 생성한다."""
        super().__init__(
            status_code=409,
            code="NICKNAME_ALREADY_EXISTS",
            message="이미 사용 중인 닉네임입니다.",
            details={"nickname": nickname},
        )


class InvalidProfileSelectionError(AppException):
    """존재하지 않거나 비활성화된 프로필 기준정보를 선택할 때 발생하는 예외."""

    def __init__(self, item_type: str, invalid_ids: list[int]) -> None:
        """선택 유형과 잘못된 식별자 목록을 포함해 예외를 생성한다."""
        super().__init__(
            status_code=422,
            code="INVALID_PROFILE_SELECTION",
            message="선택한 프로필 항목을 사용할 수 없습니다.",
            details={"item_type": item_type, "invalid_ids": invalid_ids},
        )


class InvalidProfileDateRangeError(AppException):
    """참여 가능 종료일이 시작일보다 빠를 때 발생하는 예외."""

    def __init__(self) -> None:
        """잘못된 참여 가능 날짜 범위를 공통 오류 형식으로 생성한다."""
        super().__init__(
            status_code=400,
            code="INVALID_PROFILE_DATE_RANGE",
            message="참여 가능 종료일은 시작일보다 빠를 수 없습니다.",
            details=None,
        )
