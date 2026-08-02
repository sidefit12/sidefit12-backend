"""인증 API의 요청 및 응답 Pydantic schema 모듈."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


def to_camel(value: str) -> str:
    """Python snake_case 필드명을 API camelCase 필드명으로 변환한다."""
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class CamelModel(BaseModel):
    """API JSON 필드에 camelCase alias를 적용하는 공통 schema."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class AvailabilityData(CamelModel):
    """이메일 또는 닉네임 사용 가능 여부 응답 본문."""

    available: bool
    message: str
    reason_code: str | None = None


class AvailabilityResponse(CamelModel):
    """이메일 또는 닉네임 사용 가능 여부 공통 응답."""

    success: bool = True
    data: AvailabilityData

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "available": True,
                    "message": "사용 가능한 이메일입니다.",
                    "reasonCode": None,
                },
            }
        },
    )


class SignUpRequest(CamelModel):
    """회원가입 요청 데이터."""

    email: EmailStr
    nickname: str = Field(min_length=2, max_length=15)
    password: str = Field(min_length=8, max_length=64)
    password_confirm: str = Field(min_length=8, max_length=64)
    verification_token: str = Field(min_length=1)
    terms_service_required: bool = True
    terms_privacy_required: bool = True
    terms_marketing_optional: bool = False

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "nickname": "sidefitter",
                "password": "P@ssw0rd!",
                "passwordConfirm": "P@ssw0rd!",
                "verificationToken": "evt_xxx",
                "termsServiceRequired": True,
                "termsPrivacyRequired": True,
                "termsMarketingOptional": False,
            }
        },
    )

    @model_validator(mode="after")
    def validate_signup(self):
        """비밀번호 일치 여부와 필수 약관 동의 여부를 검증한다."""
        if self.password != self.password_confirm:
            raise ValueError("password and passwordConfirm must match")
        if not self.terms_service_required or not self.terms_privacy_required:
            raise ValueError("required terms must be accepted")
        return self


class LoginRequest(CamelModel):
    """이메일 로그인 요청 데이터."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    device_info: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "P@ssw0rd!",
                "deviceInfo": "Chrome/Windows",
            }
        },
    )


class RefreshRequest(CamelModel):
    """액세스 토큰 재발급 요청 데이터."""

    refresh_token: str = Field(min_length=1)
    device_info: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={"example": {"refreshToken": "rt_xxx", "deviceInfo": "Chrome/Windows"}},
    )


class LogoutRequest(CamelModel):
    """로그아웃 요청 데이터."""

    refresh_token: str = Field(min_length=1)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={"example": {"refreshToken": "rt_xxx"}},
    )


class EmailVerificationRequest(CamelModel):
    """이메일 인증 코드 발송 요청 데이터."""

    email: EmailStr
    verification_type: str = "SIGN_UP"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={"example": {"email": "user@example.com", "verificationType": "SIGN_UP"}},
    )


class EmailVerificationConfirmRequest(CamelModel):
    """이메일 인증 코드 확인 요청 데이터."""

    email: EmailStr
    code: str = Field(min_length=6, max_length=100)
    verification_type: str = "SIGN_UP"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "code": "123456",
                "verificationType": "SIGN_UP",
            }
        },
    )


class PasswordResetRequest(CamelModel):
    """비밀번호 재설정 메일 발송 요청 데이터."""

    email: EmailStr

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={"example": {"email": "user@example.com"}},
    )


class PasswordResetConfirmRequest(CamelModel):
    """재설정 토큰을 사용한 새 비밀번호 저장 요청 데이터."""

    new_password: str = Field(min_length=8, max_length=64)
    new_password_confirm: str = Field(min_length=8, max_length=64)
    reset_token: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "newPassword": "N3wP@ssword!",
                "newPasswordConfirm": "N3wP@ssword!",
                "resetToken": "prt_xxx",
            }
        },
    )

    @model_validator(mode="after")
    def validate_password_confirmation(self):
        """새 비밀번호와 확인 값이 같은지 검증한다."""
        if self.new_password != self.new_password_confirm:
            raise ValueError("newPassword and newPasswordConfirm must match")
        return self


class PasswordResetRequestData(CamelModel):
    """비밀번호 재설정 요청 접수 결과 데이터."""

    message: str


class PasswordResetRequestResponse(CamelModel):
    """계정 존재 여부를 노출하지 않는 비밀번호 재설정 요청 응답."""

    success: bool = True
    data: PasswordResetRequestData

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"message": "입력한 이메일로 비밀번호 재설정 안내를 발송했습니다."},
            }
        },
    )


class VerificationDispatchData(CamelModel):
    """이메일 인증 코드 발송 결과 데이터."""

    verification_id: int
    expires_at: str
    resend_available_at: str


class VerificationDispatchResponse(CamelModel):
    """이메일 인증 코드 발송 응답."""

    success: bool = True
    data: VerificationDispatchData

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "verificationId": 77,
                    "expiresAt": "2026-08-02T12:10:00Z",
                    "resendAvailableAt": "2026-08-02T12:01:00Z",
                },
            }
        },
    )


class VerificationConfirmData(CamelModel):
    """이메일 인증 완료 결과 데이터."""

    expires_at: str
    verification_token: str
    verified: bool


class VerificationConfirmResponse(CamelModel):
    """이메일 인증 코드 확인 응답."""

    success: bool = True
    data: VerificationConfirmData

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "expiresAt": "2026-08-02T12:10:00Z",
                    "verificationToken": "evt_xxx",
                    "verified": True,
                },
            }
        },
    )


class UserSummary(CamelModel):
    """인증 응답에 포함하는 사용자 요약 정보."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    user_id: int
    email: EmailStr | None
    nickname: str
    user_status: str
    system_role: str
    onboarding_completed: bool = False
    profile_image_url: str | None = None


class AuthData(CamelModel):
    """사용자 정보와 인증 토큰을 포함하는 인증 응답 본문."""

    access_token: str
    expires_in: int
    refresh_token: str
    token_type: str = "Bearer"
    user: UserSummary


class AuthResponse(CamelModel):
    """회원가입 및 로그인 공통 응답."""

    success: bool = True
    data: AuthData

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "accessToken": "at_xxx",
                    "expiresIn": 1800,
                    "refreshToken": "rt_xxx",
                    "tokenType": "Bearer",
                    "user": {
                        "userId": 1,
                        "email": "user@example.com",
                        "nickname": "sidefitter",
                        "userStatus": "ACTIVE",
                        "systemRole": "USER",
                        "onboardingCompleted": False,
                        "profileImageUrl": None,
                    },
                },
            }
        },
    )


class TokenData(CamelModel):
    """토큰 재발급 응답 본문."""

    access_token: str
    expires_in: int
    refresh_token: str


class TokenResponse(CamelModel):
    """토큰 재발급 공통 응답."""

    success: bool = True
    data: TokenData

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"accessToken": "at_new", "expiresIn": 1800, "refreshToken": "rt_new"},
            }
        },
    )


class CurrentUserResponse(CamelModel):
    """현재 로그인 사용자 조회 응답."""

    success: bool = True
    data: dict[str, UserSummary]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "user": {
                        "userId": 1,
                        "email": "user@example.com",
                        "nickname": "sidefitter",
                        "userStatus": "ACTIVE",
                        "systemRole": "USER",
                        "onboardingCompleted": False,
                        "profileImageUrl": None,
                    }
                },
            }
        },
    )
