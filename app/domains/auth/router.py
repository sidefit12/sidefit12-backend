"""인증 관련 HTTP endpoint와 OpenAPI 문서 정보를 정의하는 router 모듈."""

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.schemas import (
    AuthResponse,
    AvailabilityResponse,
    CurrentUserResponse,
    EmailVerificationConfirmRequest,
    EmailVerificationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    SignUpRequest,
    TokenResponse,
    VerificationConfirmResponse,
    VerificationDispatchResponse,
)
from app.domains.auth.service import AuthService, to_summary

router = APIRouter(prefix="/auth", tags=["인증"])


def client_ip(request: Request) -> str | None:
    """요청 연결 정보에서 클라이언트 IP를 반환한다."""
    return request.client.host if request.client else None


VALIDATION_ERROR = {
    "description": "입력값을 확인해 주세요.",
    "content": {
        "application/json": {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "입력값을 확인해 주세요.",
                "details": [],
            }
        }
    },
}
AUTHENTICATION_REQUIRED = {
    "description": "로그인이 필요합니다.",
    "content": {
        "application/json": {
            "example": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "로그인이 필요합니다.",
                "details": None,
            }
        }
    },
}
INVALID_CREDENTIALS = {
    "description": "이메일 또는 비밀번호를 확인해 주세요.",
    "content": {
        "application/json": {
            "example": {
                "code": "INVALID_CREDENTIALS",
                "message": "이메일 또는 비밀번호를 확인해 주세요.",
                "details": None,
            }
        }
    },
}


@router.get(
    "/email-availability",
    response_model=AvailabilityResponse,
    summary="이메일 사용 가능 여부 확인",
    description="가입 가능한 이메일인지 확인한다. 이메일은 trim 후 소문자로 비교한다.",
    operation_id="AUTH_001_email_availability",
    responses={400: VALIDATION_ERROR, 409: {"description": "이미 사용 중인 이메일입니다."}},
)
def email_availability(
    email: str = Query(
        ..., max_length=255, description="확인할 이메일", examples=["user@example.com"]
    ),
    db: Session = Depends(get_db),
):
    """가입에 사용할 이메일의 중복 여부를 확인한다."""
    return {"data": AuthService.email_availability(db, email)}


@router.get(
    "/nickname-availability",
    response_model=AvailabilityResponse,
    summary="닉네임 사용 가능 여부 확인",
    description="닉네임 정책과 중복 여부를 확인한다.",
    operation_id="AUTH_002_nickname_availability",
    responses={400: VALIDATION_ERROR, 409: {"description": "이미 사용 중인 닉네임입니다."}},
)
def nickname_availability(
    nickname: str = Query(
        ..., min_length=2, max_length=15, description="확인할 닉네임", examples=["sidefitter"]
    ),
    db: Session = Depends(get_db),
):
    """가입에 사용할 닉네임의 중복 여부를 확인한다."""
    return {"data": AuthService.nickname_availability(db, nickname)}


@router.post(
    "/email-verifications",
    response_model=VerificationDispatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="이메일 인증 코드 발송",
    description="회원가입 또는 비밀번호 재설정을 위한 인증 코드를 발송한다.",
    operation_id="AUTH_003_dispatch_email_verification",
    responses={
        400: VALIDATION_ERROR,
        429: {"description": "요청이 너무 많습니다."},
        503: {"description": "이메일 발송을 처리할 수 없습니다."},
    },
)
def dispatch_verification(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """이메일 인증 코드를 생성해 Maileroo로 발송한다."""
    return {"data": AuthService.dispatch_verification(db, request)}


@router.post(
    "/email-verifications/confirm",
    response_model=VerificationConfirmResponse,
    summary="이메일 인증 코드 확인",
    description="사용자가 입력한 인증 코드를 확인하고 후속 요청용 일회성 토큰을 발급한다.",
    operation_id="AUTH_004_confirm_email_verification",
    responses={
        422: {"description": "인증 코드가 올바르지 않거나 만료되었습니다."},
        429: {"description": "인증 시도 횟수를 초과했습니다."},
    },
)
def confirm_verification(request: EmailVerificationConfirmRequest, db: Session = Depends(get_db)):
    """사용자가 전달한 이메일 인증 코드를 검증한다."""
    return {"data": AuthService.confirm_verification(db, request)}


@router.post(
    "/sign-up",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="이메일 회원가입",
    description="이메일 인증이 완료된 사용자를 생성하고 인증 토큰을 발급한다.",
    operation_id="AUTH_005_sign_up",
    responses={
        400: VALIDATION_ERROR,
        409: {"description": "이메일 또는 닉네임이 이미 존재합니다."},
        422: {"description": "이메일 인증이 필요합니다."},
    },
)
def signup(payload: SignUpRequest, request: Request, db: Session = Depends(get_db)):
    """회원가입을 처리하고 access/refresh token을 반환한다."""
    return {"data": AuthService.signup(db, payload, ip_address=client_ip(request))}


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="이메일 로그인",
    description="이메일과 비밀번호를 확인하고 access/refresh token을 발급한다.",
    operation_id="AUTH_006_login",
    responses={401: INVALID_CREDENTIALS, 403: {"description": "정지되거나 탈퇴한 계정입니다."}},
)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """이메일 로그인 요청을 처리하고 access/refresh token을 반환한다."""
    return {"data": AuthService.login(db, payload, ip_address=client_ip(request))}


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    summary="토큰 재발급",
    description="유효한 refresh token을 검증하고 새 토큰 쌍을 발급한다.",
    operation_id="AUTH_007_refresh_token",
    responses={401: {"description": "인증 토큰이 유효하지 않거나 만료되었습니다."}},
)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    """refresh token을 검증하고 새 토큰 쌍을 반환한다."""
    return {"data": AuthService.refresh(db, payload, ip_address=client_ip(request))}


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="로그아웃",
    description="현재 사용자의 refresh token 세션을 종료한다.",
    operation_id="AUTH_008_logout",
    responses={401: AUTHENTICATION_REQUIRED},
)
def logout(
    payload: LogoutRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """인증된 사용자의 로그아웃 요청을 처리한다."""
    AuthService.logout(db, user=user, refresh_token=payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="현재 로그인 사용자 조회",
    description="현재 access token에 연결된 사용자 요약 정보를 반환한다.",
    operation_id="AUTH_009_current_user",
    responses={401: AUTHENTICATION_REQUIRED, 404: {"description": "사용자를 찾을 수 없습니다."}},
)
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """현재 access token의 사용자 정보를 반환한다."""
    return {"data": {"user": to_summary(db, user)}}


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="비밀번호 재설정 요청",
    description="가입 여부를 노출하지 않고 일회용 비밀번호 재설정 링크 발송을 접수한다.",
    operation_id="AUTH_010_request_password_reset",
    responses={
        400: VALIDATION_ERROR,
        503: {"description": "이메일 발송을 처리할 수 없습니다."},
    },
)
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """비밀번호 재설정 요청을 접수하고 항상 동일한 안내 응답을 반환한다."""
    return {"data": AuthService.request_password_reset(db, request)}


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="비밀번호 재설정 확정",
    description="일회용 재설정 토큰을 검증하고 비밀번호를 변경한 뒤 기존 세션을 폐기한다.",
    operation_id="AUTH_011_confirm_password_reset",
    responses={
        400: VALIDATION_ERROR,
        422: {"description": "재설정 토큰이 유효하지 않거나 만료되었습니다."},
    },
)
def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
):
    """새 비밀번호를 저장하고 성공 시 응답 본문 없이 반환한다."""
    AuthService.confirm_password_reset(db, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
