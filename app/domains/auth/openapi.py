"""인증 API의 Swagger 요청·응답 예시."""

from app.core.openapi import apply_examples

USER = {
    "userId": 1,
    "email": "user@example.com",
    "nickname": "sidefitter",
    "userStatus": "ACTIVE",
    "systemRole": "USER",
    "onboardingCompleted": False,
    "profileImageUrl": None,
}
TOKEN = {
    "accessToken": "at_xxx",
    "refreshToken": "rt_xxx",
    "tokenType": "Bearer",
    "expiresIn": 1800,
    "user": USER,
}

REQUEST_EXAMPLES = {
    "AUTH_003_dispatch_email_verification": {
        "email": "user@example.com",
        "verificationType": "SIGN_UP",
    },
    "AUTH_004_confirm_email_verification": {
        "email": "user@example.com",
        "code": "123456",
        "verificationType": "SIGN_UP",
    },
    "AUTH_005_sign_up": {
        "email": "user@example.com",
        "nickname": "sidefitter",
        "password": "P@ssw0rd!",
        "passwordConfirm": "P@ssw0rd!",
        "verificationToken": "evt_xxx",
        "termsServiceRequired": True,
        "termsPrivacyRequired": True,
        "termsMarketingOptional": False,
    },
    "AUTH_006_login": {
        "email": "user@example.com",
        "password": "P@ssw0rd!",
        "deviceInfo": "Chrome/Windows",
    },
    "AUTH_007_refresh_token": {"refreshToken": "rt_xxx", "deviceInfo": "Chrome/Windows"},
    "AUTH_008_logout": {"refreshToken": "rt_xxx"},
    "AUTH_010_request_password_reset": {"email": "user@example.com"},
    "AUTH_011_confirm_password_reset": {
        "newPassword": "N3wP@ssword!",
        "newPasswordConfirm": "N3wP@ssword!",
        "resetToken": "prt_xxx",
    },
    "AUTH_012_withdraw": {"confirmation": "WITHDRAW", "password": "P@ssw0rd!"},
}
SUCCESS_EXAMPLES = {
    "AUTH_001_email_availability": {
        "success": True,
        "data": {"available": True, "message": "사용 가능한 이메일입니다.", "reasonCode": None},
    },
    "AUTH_002_nickname_availability": {
        "success": True,
        "data": {"available": True, "message": "사용 가능한 닉네임입니다.", "reasonCode": None},
    },
    "AUTH_003_dispatch_email_verification": {
        "success": True,
        "data": {
            "verificationId": 77,
            "expiresAt": "2026-08-02T05:05:00Z",
            "resendAvailableAt": "2026-08-02T05:01:00Z",
        },
    },
    "AUTH_004_confirm_email_verification": {
        "success": True,
        "data": {
            "verified": True,
            "verificationToken": "evt_xxx",
            "expiresAt": "2026-08-02T05:15:00Z",
        },
    },
    "AUTH_005_sign_up": {"success": True, "data": TOKEN},
    "AUTH_006_login": {"success": True, "data": TOKEN},
    "AUTH_007_refresh_token": {
        "success": True,
        "data": {
            "accessToken": "at_new",
            "refreshToken": "rt_new",
            "tokenType": "Bearer",
            "expiresIn": 1800,
        },
    },
    "AUTH_009_current_user": {"success": True, "data": {"user": USER}},
    "AUTH_010_request_password_reset": {
        "success": True,
        "data": {"message": "요청을 접수했습니다."},
    },
}
OPERATION_IDS = {
    f"AUTH_{number:03d}_{suffix}"
    for number, suffix in [
        (1, "email_availability"),
        (2, "nickname_availability"),
        (3, "dispatch_email_verification"),
        (4, "confirm_email_verification"),
        (5, "sign_up"),
        (6, "login"),
        (7, "refresh_token"),
        (8, "logout"),
        (9, "current_user"),
        (10, "request_password_reset"),
        (11, "confirm_password_reset"),
        (12, "withdraw"),
    ]
}


def apply_auth_openapi(schema: dict) -> dict:
    """인증 API 예시를 OpenAPI 문서에 적용한다."""
    return apply_examples(
        schema,
        operation_ids=OPERATION_IDS,
        request_examples=REQUEST_EXAMPLES,
        success_examples=SUCCESS_EXAMPLES,
    )
