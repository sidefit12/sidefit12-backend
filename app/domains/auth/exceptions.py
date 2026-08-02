"""인증 도메인에서 사용하는 커스텀 예외 모듈."""

from app.core.exceptions import AppException


class EmailAlreadyExistsError(AppException):
    """이미 등록된 이메일로 회원가입을 시도할 때 발생하는 예외."""

    def __init__(self, email: str) -> None:
        """중복 이메일 정보를 포함한 예외를 생성한다."""
        super().__init__(
            status_code=409,
            code="EMAIL_ALREADY_EXISTS",
            message="이미 사용 중인 이메일입니다.",
            details={"email": email},
        )


class NicknameAlreadyExistsError(AppException):
    """이미 등록된 닉네임으로 회원가입을 시도할 때 발생하는 예외."""

    def __init__(self, nickname: str) -> None:
        """중복 닉네임 정보를 포함한 예외를 생성한다."""
        super().__init__(
            status_code=409,
            code="NICKNAME_ALREADY_EXISTS",
            message="이미 사용 중인 닉네임입니다.",
            details={"nickname": nickname},
        )


class InvalidCredentialsError(AppException):
    """이메일 또는 비밀번호가 일치하지 않을 때 발생하는 예외."""

    def __init__(self) -> None:
        """인증정보 오류 예외를 생성한다."""
        super().__init__(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="이메일 또는 비밀번호를 확인해 주세요.",
        )


class UserSuspendedError(AppException):
    """정지된 사용자가 인증을 시도할 때 발생하는 예외."""

    def __init__(self) -> None:
        """정지 계정 예외를 생성한다."""
        super().__init__(status_code=403, code="USER_SUSPENDED", message="정지된 계정입니다.")


class UserWithdrawnError(AppException):
    """탈퇴한 사용자가 인증을 시도할 때 발생하는 예외."""

    def __init__(self) -> None:
        """탈퇴 계정 예외를 생성한다."""
        super().__init__(status_code=403, code="USER_WITHDRAWN", message="탈퇴한 계정입니다.")


class InvalidTokenError(AppException):
    """인증 토큰의 형식이나 서명이 올바르지 않을 때 발생하는 예외."""

    def __init__(self) -> None:
        """유효하지 않은 토큰 예외를 생성한다."""
        super().__init__(
            status_code=401, code="INVALID_TOKEN", message="인증 토큰이 유효하지 않습니다."
        )


class TokenExpiredError(AppException):
    """인증 토큰의 유효 기간이 만료되었을 때 발생하는 예외."""

    def __init__(self) -> None:
        """만료 토큰 예외를 생성한다."""
        super().__init__(
            status_code=401, code="TOKEN_EXPIRED", message="인증 토큰이 만료되었습니다."
        )


class RefreshTokenReusedError(AppException):
    """이미 사용되었거나 폐기된 refresh token이 재사용될 때 발생하는 예외."""

    def __init__(self) -> None:
        """refresh token 재사용 예외를 생성한다."""
        super().__init__(
            status_code=401, code="REFRESH_TOKEN_REUSED", message="세션을 다시 확인해 주세요."
        )


class AuthenticationRequiredError(AppException):
    """인증이 필요한 API에 인증 없이 접근할 때 발생하는 예외."""

    def __init__(self) -> None:
        """인증 필요 예외를 생성한다."""
        super().__init__(
            status_code=401, code="AUTHENTICATION_REQUIRED", message="로그인이 필요합니다."
        )


class EmailVerificationRequiredError(AppException):
    """이메일 인증 없이 회원가입을 시도할 때 발생하는 예외."""

    def __init__(self) -> None:
        """이메일 인증 필요 예외를 생성한다."""
        super().__init__(
            status_code=422, code="EMAIL_VERIFICATION_REQUIRED", message="이메일 인증이 필요합니다."
        )


class InvalidVerificationCodeError(AppException):
    """이메일 인증 코드가 일치하지 않을 때 발생하는 예외."""

    def __init__(self) -> None:
        """잘못된 인증 코드 예외를 생성한다."""
        super().__init__(
            status_code=422,
            code="INVALID_VERIFICATION_CODE",
            message="인증 코드가 올바르지 않습니다.",
        )


class EmailVerificationCodeExpiredError(AppException):
    """이메일 인증 코드의 유효 기간이 만료될 때 발생하는 예외."""

    def __init__(self) -> None:
        """만료된 인증 코드 예외를 생성한다."""
        super().__init__(
            status_code=422,
            code="EMAIL_VERIFICATION_CODE_EXPIRED",
            message="인증 코드가 만료되었습니다.",
        )


class InvalidPasswordResetTokenError(AppException):
    """비밀번호 재설정 토큰이 유효하지 않거나 사용됐을 때 발생하는 예외."""

    def __init__(self) -> None:
        """유효하지 않은 재설정 토큰 예외를 생성한다."""
        super().__init__(
            status_code=422,
            code="INVALID_PASSWORD_RESET_TOKEN",
            message="비밀번호 재설정 토큰이 유효하지 않습니다.",
        )


class PasswordResetTokenExpiredError(AppException):
    """비밀번호 재설정 토큰의 유효 기간이 만료됐을 때 발생하는 예외."""

    def __init__(self) -> None:
        """만료된 재설정 토큰 예외를 생성한다."""
        super().__init__(
            status_code=422,
            code="PASSWORD_RESET_TOKEN_EXPIRED",
            message="비밀번호 재설정 토큰이 만료되었습니다.",
        )


class TooManyRequestsError(AppException):
    """짧은 시간에 허용된 횟수보다 많은 요청이 들어올 때 발생하는 예외."""

    def __init__(self) -> None:
        """요청 횟수 초과 예외를 생성한다."""
        super().__init__(
            status_code=429,
            code="TOO_MANY_REQUESTS",
            message="요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.",
        )


class EmailDeliveryUnavailableError(AppException):
    """이메일 발송 외부 서비스가 사용할 수 없을 때 발생하는 예외."""

    def __init__(self) -> None:
        """이메일 발송 불가 예외를 생성한다."""
        super().__init__(
            status_code=503,
            code="EMAIL_DELIVERY_UNAVAILABLE",
            message="이메일 발송을 일시적으로 처리할 수 없습니다.",
        )


class InvalidStateTransitionError(AppException):
    """현재 사용자 상태에서 요청한 상태 변경이 허용되지 않을 때 발생하는 예외."""

    def __init__(self) -> None:
        """상태 변경 불가 예외를 생성한다."""
        super().__init__(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message="현재 상태에서는 요청을 처리할 수 없습니다.",
        )


class AuthUserNotFoundError(AppException):
    """토큰에 해당하는 사용자를 찾을 수 없을 때 발생하는 예외."""

    def __init__(self, user_id: int) -> None:
        """조회에 실패한 사용자 식별자를 포함한 예외를 생성한다."""
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
            details={"user_id": user_id},
        )
