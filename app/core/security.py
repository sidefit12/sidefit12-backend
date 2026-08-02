"""JWT 발급과 비밀번호 해싱을 담당하는 인증 보안 모듈."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """평문 비밀번호를 Argon2 기반 해시 문자열로 변환한다."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """평문 비밀번호가 저장된 해시와 일치하는지 검증한다."""
    return password_hash.verify(password, hashed_password)


def create_token(subject: int, *, token_type: str, expires_delta: timedelta) -> str:
    """사용자 식별자와 토큰 종류를 포함한 JWT를 발급한다."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, get_settings().jwt_secret_key, algorithm="HS256")


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    """JWT 서명, 만료 시간, 토큰 종류를 검증한 뒤 payload를 반환한다."""
    payload = jwt.decode(
        token,
        get_settings().jwt_secret_key,
        algorithms=["HS256"],
    )
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise jwt.InvalidTokenError("invalid token type")
    return payload
