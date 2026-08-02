"""사용자 API 요청 및 응답 스키마를 정의하는 모듈."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    """사용자 조회 응답."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    user_id: int
    email: EmailStr
    nickname: str
    user_status: str
    system_role: str
    email_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
