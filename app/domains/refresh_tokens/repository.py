"""리프레시 토큰 데이터 접근 repository."""

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domains.refresh_tokens.models import RefreshToken


class RefreshTokenRepository:
    """리프레시 토큰 세션의 조회, 저장 및 폐기를 담당한다."""

    @staticmethod
    def find_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
        """토큰 해시로 저장된 세션을 조회한다."""
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
        """새 리프레시 토큰 세션을 추가한다."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )
        db.add(token)
        db.flush()
        return token

    @staticmethod
    def revoke(db: Session, token: RefreshToken, revoked_at: datetime) -> None:
        """단일 리프레시 토큰 세션을 폐기한다."""
        token.last_used_at = revoked_at
        token.revoked_at = revoked_at
        db.add(token)

    @staticmethod
    def revoke_all_by_user_id(db: Session, user_id: int, revoked_at: datetime) -> None:
        """사용자의 활성 리프레시 토큰 세션을 모두 폐기한다."""
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(last_used_at=revoked_at, revoked_at=revoked_at)
        )
