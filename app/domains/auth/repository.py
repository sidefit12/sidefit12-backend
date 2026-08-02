"""인증 세션 데이터의 영속성 접근을 담당하는 repository 모듈."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domains.auth.models import RefreshToken


class RefreshTokenRepository:
    """refresh token 세션의 조회, 저장 및 폐기 연산을 제공한다."""

    @staticmethod
    def find_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
        """refresh token 해시로 저장된 세션을 조회한다."""
        return db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    @staticmethod
    def add(
        db: Session,
        *,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        device_info: str | None,
        ip_address: str | None,
    ) -> RefreshToken:
        """새 refresh token 세션을 session에 추가한다."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )
        db.add(refresh_token)
        db.flush()
        return refresh_token

    @staticmethod
    def revoke(db: Session, refresh_token: RefreshToken, revoked_at: datetime) -> None:
        """단일 refresh token 세션을 폐기한다."""
        refresh_token.last_used_at = revoked_at
        refresh_token.revoked_at = revoked_at
        db.add(refresh_token)

    @staticmethod
    def revoke_all_by_user_id(db: Session, user_id: int, revoked_at: datetime) -> None:
        """사용자의 폐기되지 않은 모든 refresh token 세션을 폐기한다."""
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(last_used_at=revoked_at, revoked_at=revoked_at)
        )
