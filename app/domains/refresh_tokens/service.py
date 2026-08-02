"""리프레시 토큰 세션 서비스."""

from app.domains.refresh_tokens.repository import RefreshTokenRepository


class RefreshTokenService:
    """auth 흐름에 리프레시 토큰 세션 연산을 제공한다."""

    find_by_hash = staticmethod(RefreshTokenRepository.find_by_hash)
    create = staticmethod(RefreshTokenRepository.add)
    revoke = staticmethod(RefreshTokenRepository.revoke)
    revoke_all_by_user_id = staticmethod(RefreshTokenRepository.revoke_all_by_user_id)
