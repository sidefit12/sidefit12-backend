"""인증 API의 정상 흐름과 주요 실패 응답을 검증하는 테스트."""

from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.auth.models import EmailVerification, RefreshToken
from app.domains.auth.service import AuthService
from app.domains.users.models import User
from tests.conftest import SentEmailStore


EMAIL = "tester@example.com"
PASSWORD = "StrongPassword1!"


def dispatch_and_confirm(client: TestClient, sent_emails: SentEmailStore) -> str:
    """회원가입 이메일을 발송하고 인증 토큰까지 발급받는다."""
    dispatch_response = client.post(
        "/api/v1/auth/email-verifications",
        json={"email": EMAIL, "verificationType": "SIGN_UP"},
    )
    assert dispatch_response.status_code == 202
    assert dispatch_response.json()["data"]["verificationId"] > 0
    assert len(sent_emails.messages) == 1

    confirm_response = client.post(
        "/api/v1/auth/email-verifications/confirm",
        json={"email": EMAIL, "code": sent_emails.latest_code, "verificationType": "SIGN_UP"},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["data"]["verified"] is True
    return confirm_response.json()["data"]["verificationToken"]


def signup(client: TestClient, verification_token: str) -> dict:
    """인증 토큰으로 회원가입하고 응답 데이터를 반환한다."""
    response = client.post(
        "/api/v1/auth/sign-up",
        json={
            "email": EMAIL,
            "nickname": "sidefitter",
            "password": PASSWORD,
            "passwordConfirm": PASSWORD,
            "verificationToken": verification_token,
            "termsServiceRequired": True,
            "termsPrivacyRequired": True,
            "termsMarketingOptional": False,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_complete_auth_flow(
    client: TestClient,
    db_session: Session,
    sent_emails: SentEmailStore,
) -> None:
    """이메일 인증부터 로그인과 Bearer 사용자 조회까지 전체 흐름을 검증한다."""
    verification_token = dispatch_and_confirm(client, sent_emails)
    signup_data = signup(client, verification_token)
    assert signup_data["user"]["email"] == EMAIL
    assert signup_data["tokenType"] == "Bearer"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD, "deviceInfo": "pytest"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()["data"]

    db_session.expire_all()
    user = db_session.scalar(select(User).where(User.email == EMAIL))
    assert user is not None
    assert isinstance(user.last_login_at, datetime)

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_data['accessToken']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["user"]["userId"] == user.user_id

    refresh_response = client.post(
        "/api/v1/auth/token/refresh",
        json={"refreshToken": login_data["refreshToken"], "deviceInfo": "pytest"},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["accessToken"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_data['accessToken']}"},
        json={"refreshToken": login_data["refreshToken"]},
    )
    assert logout_response.status_code == 204


def test_duplicate_availability_after_signup(
    client: TestClient, sent_emails: SentEmailStore
) -> None:
    """가입된 이메일과 닉네임이 중복으로 표시되는지 확인한다."""
    signup(client, dispatch_and_confirm(client, sent_emails))

    email_response = client.get("/api/v1/auth/email-availability", params={"email": EMAIL})
    nickname_response = client.get(
        "/api/v1/auth/nickname-availability", params={"nickname": "sidefitter"}
    )

    assert email_response.json()["data"]["available"] is False
    assert email_response.json()["data"]["reasonCode"] == "EMAIL_ALREADY_EXISTS"
    assert nickname_response.json()["data"]["available"] is False
    assert nickname_response.json()["data"]["reasonCode"] == "NICKNAME_ALREADY_EXISTS"


def test_verification_resend_is_limited(client: TestClient, sent_emails: SentEmailStore) -> None:
    """같은 이메일의 60초 이내 인증번호 재발송을 차단한다."""
    payload = {"email": EMAIL, "verificationType": "SIGN_UP"}
    assert client.post("/api/v1/auth/email-verifications", json=payload).status_code == 202

    response = client.post("/api/v1/auth/email-verifications", json=payload)

    assert response.status_code == 429
    assert response.json()["code"] == "TOO_MANY_REQUESTS"
    assert len(sent_emails.messages) == 1


def test_invalid_verification_code_increases_attempt_count(
    client: TestClient,
    db_session: Session,
) -> None:
    """잘못된 인증번호 요청이 실패하고 시도 횟수가 증가하는지 확인한다."""
    client.post(
        "/api/v1/auth/email-verifications",
        json={"email": EMAIL, "verificationType": "SIGN_UP"},
    )
    response = client.post(
        "/api/v1/auth/email-verifications/confirm",
        json={"email": EMAIL, "code": "000000", "verificationType": "SIGN_UP"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_VERIFICATION_CODE"
    verification = db_session.scalar(
        select(EmailVerification).where(EmailVerification.email == EMAIL)
    )
    assert verification is not None
    assert verification.attempt_count == 1


def test_login_rejects_wrong_password(client: TestClient, sent_emails: SentEmailStore) -> None:
    """잘못된 비밀번호 로그인에 공통 인증 오류를 반환한다."""
    signup(client, dispatch_and_confirm(client, sent_emails))
    response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": "WrongPassword1!"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_me_requires_bearer_token(client: TestClient) -> None:
    """현재 사용자 조회 API가 Bearer 인증을 요구하는지 확인한다."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_openapi_registers_http_bearer(client: TestClient) -> None:
    """Swagger에 JWT HTTP Bearer 방식이 등록되는지 확인한다."""
    schema = client.get("/openapi.json").json()
    bearer = schema["components"]["securitySchemes"]["BearerAuth"]
    assert bearer["type"] == "http"
    assert bearer["scheme"] == "bearer"
    assert bearer["bearerFormat"] == "JWT"
    assert schema["paths"]["/api/v1/auth/me"]["get"]["security"] == [{"BearerAuth": []}]


def test_password_reset_changes_password_and_consumes_token(
    client: TestClient,
    db_session: Session,
    sent_emails: SentEmailStore,
) -> None:
    """재설정 토큰으로 비밀번호를 변경하고 토큰을 재사용할 수 없는지 확인한다."""
    signup(client, dispatch_and_confirm(client, sent_emails))
    user = db_session.scalar(select(User).where(User.email == EMAIL))
    assert user is not None
    db_session.add(
        RefreshToken(
            user_id=user.user_id,
            token_hash="existing-refresh-token-hash",
            expires_at=datetime.now().replace(year=datetime.now().year + 1),
        )
    )
    db_session.commit()

    request_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": EMAIL},
    )
    assert request_response.status_code == 202
    assert len(sent_emails.password_resets) == 1

    reset_token = sent_emails.latest_reset_token
    verification = db_session.scalar(
        select(EmailVerification).where(EmailVerification.verification_type == "PASSWORD_RESET")
    )
    assert verification is not None
    assert verification.verification_code == AuthService._hash_value(reset_token)
    assert reset_token not in verification.verification_code

    new_password = "ChangedPassword1!"
    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "newPassword": new_password,
            "newPasswordConfirm": new_password,
            "resetToken": reset_token,
        },
    )
    assert confirm_response.status_code == 204

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": new_password},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200

    db_session.expire_all()
    refresh_token = db_session.scalar(
        select(RefreshToken).where(RefreshToken.user_id == user.user_id)
    )
    assert refresh_token is not None
    assert refresh_token.revoked_at is not None

    reused_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "newPassword": "AnotherPassword1!",
            "newPasswordConfirm": "AnotherPassword1!",
            "resetToken": reset_token,
        },
    )
    assert reused_response.status_code == 422
    assert reused_response.json()["code"] == "INVALID_PASSWORD_RESET_TOKEN"


def test_password_reset_request_does_not_reveal_unknown_email(
    client: TestClient,
    sent_emails: SentEmailStore,
) -> None:
    """가입되지 않은 이메일에도 동일한 접수 응답을 반환한다."""
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "unknown@example.com"},
    )
    assert response.status_code == 202
    assert response.json()["data"]["message"]
    assert sent_emails.password_resets == []


def test_refresh_rotation_reuse_detection_and_logout(
    client: TestClient,
    db_session: Session,
    sent_emails: SentEmailStore,
) -> None:
    """refresh token 저장·회전·재사용 탐지와 로그아웃 폐기를 검증한다."""
    signup_data = signup(client, dispatch_and_confirm(client, sent_emails))
    original_refresh = signup_data["refreshToken"]
    original_row = db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == AuthService._hash_value(original_refresh)
        )
    )
    assert original_row is not None
    assert original_row.revoked_at is None

    refresh_response = client.post(
        "/api/v1/auth/token/refresh",
        json={"refreshToken": original_refresh, "deviceInfo": "pytest-rotated"},
    )
    assert refresh_response.status_code == 200
    rotated_refresh = refresh_response.json()["data"]["refreshToken"]
    assert rotated_refresh != original_refresh

    db_session.expire_all()
    original_row = db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == AuthService._hash_value(original_refresh)
        )
    )
    rotated_row = db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == AuthService._hash_value(rotated_refresh)
        )
    )
    assert original_row is not None and original_row.revoked_at is not None
    assert rotated_row is not None and rotated_row.revoked_at is None

    reused_response = client.post(
        "/api/v1/auth/token/refresh",
        json={"refreshToken": original_refresh},
    )
    assert reused_response.status_code == 401
    assert reused_response.json()["code"] == "REFRESH_TOKEN_REUSED"
    db_session.expire_all()
    assert rotated_row.revoked_at is not None

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD, "deviceInfo": "pytest-logout"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()["data"]
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_data['accessToken']}"},
        json={"refreshToken": login_data["refreshToken"]},
    )
    assert logout_response.status_code == 204

    logged_out_row = db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == AuthService._hash_value(login_data["refreshToken"])
        )
    )
    assert logged_out_row is not None and logged_out_row.revoked_at is not None
    logged_out_refresh = client.post(
        "/api/v1/auth/token/refresh",
        json={"refreshToken": login_data["refreshToken"]},
    )
    assert logged_out_refresh.status_code == 401
    assert logged_out_refresh.json()["code"] == "REFRESH_TOKEN_REUSED"
