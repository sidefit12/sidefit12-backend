from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.users.models import User


class UserRepository:
    """사용자 데이터 접근을 담당한다."""
