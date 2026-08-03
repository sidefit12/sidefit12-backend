"""인증이 필요한 API에서 사용하는 FastAPI dependency 모듈."""

import jwt
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.domains.auth.exceptions import (
    AuthenticationRequiredError,
    AuthUserNotFoundError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.domains.users.models import User
from app.domains.users.service import UserService

bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="BearerAuth",
    description="로그인 응답의 accessToken을 입력하세요. 'Bearer' 접두사는 Swagger가 자동으로 추가합니다.",
    auto_error=False,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Bearer access token을 검증하고 현재 활성 사용자를 조회한다."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationRequiredError()

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except (ValueError, jwt.InvalidTokenError) as exc:
        raise InvalidTokenError() from exc

    user = UserService.get_by_id(db, user_id)
    if user is None or user.user_status != "ACTIVE":
        if user is None:
            raise AuthUserNotFoundError(user_id)
        raise AuthenticationRequiredError()
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Bearer 토큰이 없으면 비회원으로, 있으면 인증된 사용자로 처리한다."""
    if credentials is None:
        return None
    return get_current_user(credentials, db)
