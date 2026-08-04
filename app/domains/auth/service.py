"""회원가입, 이메일 인증, 로그인, 토큰 발급의 비즈니스 로직 모듈."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.domains.auth.exceptions import (
    EmailAlreadyExistsError,
    EmailVerificationCodeExpiredError,
    EmailVerificationRequiredError,
    InvalidCredentialsError,
    InvalidPasswordResetTokenError,
    InvalidStateTransitionError,
    InvalidTokenError,
    InvalidVerificationCodeError,
    NicknameAlreadyExistsError,
    PasswordResetTokenExpiredError,
    RefreshTokenReusedError,
    TokenExpiredError,
    TooManyRequestsError,
    UserSuspendedError,
    UserWithdrawnError,
)
from app.domains.auth.schemas import (
    AuthData,
    AvailabilityData,
    EmailVerificationConfirmRequest,
    EmailVerificationRequest,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestData,
    RefreshRequest,
    SignUpRequest,
    TokenData,
    UserSummary,
    VerificationConfirmData,
    VerificationDispatchData,
    WithdrawRequest,
)
from app.domains.email_verifications.service import EmailVerificationService
from app.domains.refresh_tokens.service import RefreshTokenService
from app.domains.users.models import User
from app.domains.users.service import UserService
from app.integrations.maileroo import MailerooEmailService

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    """users 도메인의 규칙으로 이메일을 정규화한다."""
    return UserService.normalize_email(email)


def as_utc(value: datetime) -> datetime:
    """DB에서 읽은 datetime을 UTC timezone-aware 값으로 정규화한다."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_summary(db: Session, user: User) -> UserSummary:
    """User ORM 객체를 외부 응답용 사용자 요약 schema로 변환한다."""
    from app.domains.user_profiles.repository import ProfileRepository

    profile = ProfileRepository.find_profile(db, user.user_id)
    return UserSummary(
        user_id=user.user_id,
        email=user.email,
        nickname=user.nickname,
        user_status=user.user_status,
        system_role=user.system_role,
        onboarding_completed=bool(profile and profile.onboarding_completed),
    )


class AuthService:
    """인증 API에서 사용하는 사용자, 이메일, 토큰 처리 서비스."""

    @staticmethod
    def _user_by_email(db: Session, email: str) -> User | None:
        """users service를 통해 이메일로 사용자를 조회한다."""
        return UserService.get_by_email(db, email)

    @staticmethod
    def _user_by_nickname(db: Session, nickname: str) -> User | None:
        """users service를 통해 닉네임으로 사용자를 조회한다."""
        return UserService.get_by_nickname(db, nickname)

    @staticmethod
    def withdraw(db: Session, user: User, request: WithdrawRequest) -> None:
        """비밀번호와 프로젝트 책임을 검증한 후 회원을 익명화한다."""
        from app.domains.projects.service import ProjectService
        from app.domains.user_profiles.service import ProfileService

        if user.user_status != "ACTIVE":
            raise InvalidStateTransitionError()
        if not verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError()
        if ProjectService.has_active_owned_project(db, user.user_id):
            raise InvalidStateTransitionError()
        now = datetime.now(timezone.utc)
        ProfileService.anonymize(db, user.user_id)
        RefreshTokenService.revoke_all_by_user_id(db, user.user_id, now)
        UserService.withdraw(
            user,
            withdrawn_at=now,
            password_hash=hash_password(secrets.token_urlsafe(32)),
        )
        db.commit()

    @staticmethod
    def email_availability(db: Session, email: str) -> AvailabilityData:
        """이메일 중복 여부와 API 안내 메시지를 반환한다."""
        exists = AuthService._user_by_email(db, email) is not None
        return AvailabilityData(
            available=not exists,
            message="이미 사용 중인 이메일입니다." if exists else "사용 가능한 이메일입니다.",
            reason_code="EMAIL_ALREADY_EXISTS" if exists else None,
        )

    @staticmethod
    def nickname_availability(db: Session, nickname: str) -> AvailabilityData:
        """닉네임 중복 여부와 API 안내 메시지를 반환한다."""
        exists = AuthService._user_by_nickname(db, nickname) is not None
        return AvailabilityData(
            available=not exists,
            message="이미 사용 중인 닉네임입니다." if exists else "사용 가능한 닉네임입니다.",
            reason_code="NICKNAME_ALREADY_EXISTS" if exists else None,
        )

    @staticmethod
    def dispatch_verification(
        db: Session, request: EmailVerificationRequest
    ) -> VerificationDispatchData:
        """인증 코드를 생성해 DB에 저장하고 Maileroo로 발송한다."""
        email = normalize_email(str(request.email))
        now = datetime.now(timezone.utc)
        latest = EmailVerificationService.find_latest(db, email, request.verification_type)
        if latest and latest.created_at and now - as_utc(latest.created_at) < timedelta(seconds=60):
            logger.warning(
                "이메일 인증 코드 재발송 제한에 걸렸습니다.",
                extra={
                    "event": "email_verification_rate_limited",
                    "verification_type": request.verification_type,
                },
            )
            raise TooManyRequestsError()

        code = f"{secrets.randbelow(1_000_000):06d}"
        verification = EmailVerificationService.create(
            db,
            email=email,
            verification_type=request.verification_type,
            verification_code=AuthService._hash_value(code),
            expires_at=now + timedelta(minutes=5),
        )
        maileroo = MailerooEmailService()
        try:
            maileroo.send_verification_code(to_email=email, code=code)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            maileroo.close()

        logger.info(
            "이메일 인증 코드를 발송했습니다.",
            extra={
                "event": "email_verification_dispatched",
                "verification_id": verification.email_verification_id,
                "verification_type": request.verification_type,
            },
        )

        return VerificationDispatchData(
            verification_id=verification.email_verification_id,
            expires_at=verification.expires_at.isoformat(),
            resend_available_at=(now + timedelta(seconds=60)).isoformat(),
        )

    @staticmethod
    def confirm_verification(
        db: Session, request: EmailVerificationConfirmRequest
    ) -> VerificationConfirmData:
        """인증 코드를 검증하고 회원가입에 사용할 일회성 토큰을 발급한다."""
        email = normalize_email(str(request.email))
        verification = EmailVerificationService.find_latest(db, email, request.verification_type)
        now = datetime.now(timezone.utc)
        if verification is None or verification.verified_at is not None:
            logger.warning(
                "이메일 인증 코드 확인에 실패했습니다.",
                extra={
                    "event": "email_verification_failed",
                    "verification_type": request.verification_type,
                },
            )
            raise InvalidVerificationCodeError()
        if as_utc(verification.expires_at) <= now:
            logger.warning(
                "만료된 이메일 인증 코드가 입력되었습니다.",
                extra={
                    "event": "email_verification_expired",
                    "verification_id": verification.email_verification_id,
                    "verification_type": request.verification_type,
                },
            )
            raise EmailVerificationCodeExpiredError()
        if verification.attempt_count >= 5:
            raise TooManyRequestsError()
        if verification.verification_code != AuthService._hash_value(request.code):
            EmailVerificationService.increase_attempt(db, verification)
            db.commit()
            logger.warning(
                "이메일 인증 코드가 일치하지 않습니다.",
                extra={
                    "event": "email_verification_code_mismatch",
                    "verification_id": verification.email_verification_id,
                    "verification_type": request.verification_type,
                },
            )
            raise InvalidVerificationCodeError()

        verification_token = secrets.token_urlsafe(32)
        EmailVerificationService.confirm(
            db, verification, AuthService._hash_value(verification_token), now
        )
        db.commit()
        logger.info(
            "이메일 인증이 완료되었습니다.",
            extra={
                "event": "email_verification_confirmed",
                "verification_id": verification.email_verification_id,
                "verification_type": request.verification_type,
            },
        )
        return VerificationConfirmData(
            expires_at=verification.expires_at.isoformat(),
            verification_token=verification_token,
            verified=True,
        )

    @staticmethod
    def _hash_value(value: str) -> str:
        """인증 코드 또는 인증 토큰을 저장용 SHA-256 해시로 변환한다."""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def signup(
        db: Session,
        request: SignUpRequest,
        *,
        ip_address: str | None = None,
    ) -> AuthData:
        """이메일 인증 완료 여부를 확인한 뒤 사용자를 생성하고 토큰을 발급한다."""
        email = normalize_email(str(request.email))
        nickname = request.nickname.strip()
        if AuthService._user_by_email(db, email):
            raise EmailAlreadyExistsError(email)
        if AuthService._user_by_nickname(db, nickname):
            raise NicknameAlreadyExistsError(nickname)

        verification = EmailVerificationService.find_verified_signup(db, email)
        if verification is None or verification.verification_code != AuthService._hash_value(
            request.verification_token
        ):
            raise EmailVerificationRequiredError()

        user = UserService.create_active_user(
            db,
            email=email,
            password_hash=hash_password(request.password),
            nickname=nickname,
        )
        UserService.mark_email_verified(db, user)
        EmailVerificationService.assign_user(db, verification, user.user_id)
        tokens = AuthService._create_session(
            db,
            user_id=user.user_id,
            device_info=None,
            ip_address=ip_address,
        )
        db.commit()
        UserService.refresh(db, user)
        return AuthService._auth_data(db, user, tokens)

    @staticmethod
    def login(
        db: Session,
        request: LoginRequest,
        *,
        ip_address: str | None = None,
    ) -> AuthData:
        """이메일과 비밀번호를 검증한 뒤 인증 토큰을 발급한다."""
        user = AuthService._user_by_email(db, str(request.email))
        if user is None or not verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError()
        if user.user_status == "SUSPENDED":
            raise UserSuspendedError()
        if user.user_status == "WITHDRAWN":
            raise UserWithdrawnError()
        if user.user_status != "ACTIVE":
            raise InvalidCredentialsError()

        UserService.update_last_login(db, user)
        tokens = AuthService._create_session(
            db,
            user_id=user.user_id,
            device_info=request.device_info,
            ip_address=ip_address,
        )
        db.commit()
        logger.info(
            "사용자 로그인이 완료되었습니다.",
            extra={"event": "user_login_succeeded", "user_id": user.user_id},
        )
        return AuthService._auth_data(db, user, tokens)

    @staticmethod
    def refresh(
        db: Session,
        request: RefreshRequest,
        *,
        ip_address: str | None = None,
    ) -> TokenData:
        """저장 상태를 검증한 refresh token을 폐기하고 새 토큰 쌍으로 회전한다."""
        try:
            payload = decode_token(request.refresh_token, expected_type="refresh")
            user_id = int(payload["sub"])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except (ValueError, jwt.InvalidTokenError) as exc:
            raise InvalidTokenError() from exc

        stored_token = RefreshTokenService.find_by_hash(
            db, AuthService._hash_value(request.refresh_token)
        )
        if stored_token is None:
            raise RefreshTokenReusedError()

        now = datetime.now(timezone.utc)
        if stored_token.revoked_at is not None:
            RefreshTokenService.revoke_all_by_user_id(db, stored_token.user_id, now)
            db.commit()
            raise RefreshTokenReusedError()
        if stored_token.user_id != user_id:
            raise InvalidTokenError()
        if as_utc(stored_token.expires_at) <= now:
            RefreshTokenService.revoke(db, stored_token, now)
            db.commit()
            raise TokenExpiredError()

        user = UserService.get_by_id(db, user_id)
        if user is None or user.user_status != "ACTIVE":
            raise InvalidTokenError()

        RefreshTokenService.revoke(db, stored_token, now)
        tokens = AuthService._create_session(
            db,
            user_id=user_id,
            device_info=request.device_info or stored_token.device_info,
            ip_address=ip_address or stored_token.ip_address,
        )
        db.commit()
        logger.info(
            "refresh token이 회전되었습니다.",
            extra={"event": "refresh_token_rotated", "user_id": user_id},
        )
        return tokens

    @staticmethod
    def logout(db: Session, *, user: User, refresh_token: str) -> None:
        """현재 사용자의 refresh token 세션을 폐기한다."""
        stored_token = RefreshTokenService.find_by_hash(db, AuthService._hash_value(refresh_token))
        if stored_token is not None and stored_token.user_id == user.user_id:
            if stored_token.revoked_at is None:
                RefreshTokenService.revoke(db, stored_token, datetime.now(timezone.utc))
                db.commit()
        logger.info(
            "사용자 로그아웃이 완료되었습니다.",
            extra={"event": "user_logout_succeeded", "user_id": user.user_id},
        )

    @staticmethod
    def request_password_reset(
        db: Session, request: PasswordResetRequest
    ) -> PasswordResetRequestData:
        """계정 존재 여부를 노출하지 않고 비밀번호 재설정 메일을 접수한다."""
        message = "입력한 이메일로 비밀번호 재설정 안내를 발송했습니다."
        email = normalize_email(str(request.email))
        user = UserService.get_by_email(db, email)
        if user is None or user.user_status != "ACTIVE":
            logger.info(
                "비밀번호 재설정 요청을 접수했습니다.",
                extra={"event": "password_reset_requested"},
            )
            return PasswordResetRequestData(message=message)

        now = datetime.now(timezone.utc)
        latest = EmailVerificationService.find_latest(db, email, "PASSWORD_RESET")
        if latest and latest.created_at and now - as_utc(latest.created_at) < timedelta(seconds=60):
            logger.info(
                "비밀번호 재설정 메일 재발송을 생략했습니다.",
                extra={"event": "password_reset_rate_limited", "user_id": user.user_id},
            )
            return PasswordResetRequestData(message=message)

        reset_token = f"prt_{secrets.token_urlsafe(32)}"
        verification = EmailVerificationService.create(
            db,
            user_id=user.user_id,
            email=email,
            verification_type="PASSWORD_RESET",
            verification_code=AuthService._hash_value(reset_token),
            expires_at=now + timedelta(minutes=10),
        )
        maileroo = MailerooEmailService()
        try:
            maileroo.send_password_reset(to_email=email, reset_token=reset_token)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            maileroo.close()

        logger.info(
            "비밀번호 재설정 메일을 발송했습니다.",
            extra={
                "event": "password_reset_email_dispatched",
                "user_id": user.user_id,
                "verification_id": verification.email_verification_id,
            },
        )
        return PasswordResetRequestData(message=message)

    @staticmethod
    def confirm_password_reset(db: Session, request: PasswordResetConfirmRequest) -> None:
        """일회용 재설정 토큰으로 비밀번호를 변경하고 기존 세션을 폐기한다."""
        verification = EmailVerificationService.find_password_reset(
            db, AuthService._hash_value(request.reset_token)
        )
        if verification is None or verification.user_id is None:
            raise InvalidPasswordResetTokenError()

        now = datetime.now(timezone.utc)
        if as_utc(verification.expires_at) <= now:
            raise PasswordResetTokenExpiredError()

        user = UserService.get_by_id(db, verification.user_id)
        if user is None or user.user_status != "ACTIVE":
            raise InvalidPasswordResetTokenError()

        UserService.update_password_hash(db, user, hash_password(request.new_password))
        EmailVerificationService.mark_used(db, verification, now)
        RefreshTokenService.revoke_all_by_user_id(db, user.user_id, now)
        db.commit()
        logger.info(
            "비밀번호 재설정이 완료되었습니다.",
            extra={"event": "password_reset_confirmed", "user_id": user.user_id},
        )

    @staticmethod
    def _tokens(user_id: int) -> TokenData:
        """사용자 식별자에 대한 access/refresh token 쌍을 생성한다."""
        settings = get_settings()
        return TokenData(
            access_token=create_token(
                user_id,
                token_type="access",
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
            ),
            expires_in=settings.access_token_expire_minutes * 60,
            refresh_token=create_token(
                user_id,
                token_type="refresh",
                expires_delta=timedelta(days=settings.refresh_token_expire_days),
            ),
        )

    @staticmethod
    def _create_session(
        db: Session,
        *,
        user_id: int,
        device_info: str | None,
        ip_address: str | None,
    ) -> TokenData:
        """새 토큰 쌍을 발급하고 refresh token 해시를 session에 저장한다."""
        tokens = AuthService._tokens(user_id)
        refresh_payload = decode_token(tokens.refresh_token, expected_type="refresh")
        RefreshTokenService.create(
            db,
            user_id=user_id,
            token_hash=AuthService._hash_value(tokens.refresh_token),
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
            device_info=device_info,
            ip_address=ip_address,
        )
        return tokens

    @staticmethod
    def _auth_data(db: Session, user: User, tokens: TokenData) -> AuthData:
        """발급된 토큰과 사용자 정보를 인증 응답 데이터로 구성한다."""
        return AuthData(**tokens.model_dump(), user=to_summary(db, user))
