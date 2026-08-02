"""이메일 인증 이력 서비스."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domains.email_verifications.models import EmailVerification
from app.domains.email_verifications.repository import EmailVerificationRepository


class EmailVerificationService:
    """auth 흐름에 필요한 이메일 인증 이력 연산을 제공한다."""

    find_latest = staticmethod(EmailVerificationRepository.find_latest)
    find_verified_signup = staticmethod(EmailVerificationRepository.find_verified_signup)
    find_password_reset = staticmethod(EmailVerificationRepository.find_password_reset)
    create = staticmethod(EmailVerificationRepository.add)

    @staticmethod
    def increase_attempt(db: Session, verification: EmailVerification) -> None:
        """실패한 인증 코드 입력 횟수를 증가시킨다."""
        verification.attempt_count += 1
        EmailVerificationRepository.save(db, verification)

    @staticmethod
    def confirm(
        db: Session, verification: EmailVerification, token_hash: str, now: datetime
    ) -> None:
        """인증을 완료하고 후속 흐름에서 사용할 토큰 해시를 저장한다."""
        verification.verification_code = token_hash
        verification.verified_at = now
        EmailVerificationRepository.save(db, verification)

    @staticmethod
    def assign_user(db: Session, verification: EmailVerification, user_id: int) -> None:
        """회원가입 인증 이력을 생성된 사용자에게 귀속한다."""
        verification.user_id = user_id
        EmailVerificationRepository.save(db, verification)

    @staticmethod
    def mark_used(db: Session, verification: EmailVerification, now: datetime) -> None:
        """비밀번호 재설정 인증 이력을 사용 완료 처리한다."""
        verification.verified_at = now
        EmailVerificationRepository.save(db, verification)
