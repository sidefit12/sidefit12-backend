"""이메일 인증 데이터 접근 repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.email_verifications.models import EmailVerification


class EmailVerificationRepository:
    """이메일 인증 이력의 조회와 저장을 담당한다."""

    @staticmethod
    def find_latest(db: Session, email: str, verification_type: str) -> EmailVerification | None:
        """이메일과 인증 유형에 해당하는 최신 이력을 조회한다."""
        return db.scalar(
            select(EmailVerification)
            .where(
                EmailVerification.email == email,
                EmailVerification.verification_type == verification_type,
            )
            .order_by(EmailVerification.created_at.desc())
        )

    @staticmethod
    def find_verified_signup(db: Session, email: str) -> EmailVerification | None:
        """아직 회원에게 귀속되지 않은 최신 회원가입 인증을 조회한다."""
        return db.scalar(
            select(EmailVerification)
            .where(
                EmailVerification.email == email,
                EmailVerification.verification_type == "SIGN_UP",
                EmailVerification.verified_at.is_not(None),
                EmailVerification.user_id.is_(None),
            )
            .order_by(EmailVerification.created_at.desc())
        )

    @staticmethod
    def find_password_reset(db: Session, token_hash: str) -> EmailVerification | None:
        """사용되지 않은 비밀번호 재설정 토큰 이력을 조회한다."""
        return db.scalar(
            select(EmailVerification).where(
                EmailVerification.verification_type == "PASSWORD_RESET",
                EmailVerification.verification_code == token_hash,
                EmailVerification.verified_at.is_(None),
            )
        )

    @staticmethod
    def add(
        db: Session,
        *,
        email: str,
        verification_type: str,
        verification_code: str,
        expires_at: datetime,
        user_id: int | None = None,
    ) -> EmailVerification:
        """새 이메일 인증 이력을 session에 추가한다."""
        verification = EmailVerification(
            user_id=user_id,
            email=email,
            verification_type=verification_type,
            verification_code=verification_code,
            expires_at=expires_at,
        )
        db.add(verification)
        db.flush()
        return verification

    @staticmethod
    def save(db: Session, verification: EmailVerification) -> None:
        """변경된 이메일 인증 이력을 session에 반영한다."""
        db.add(verification)
