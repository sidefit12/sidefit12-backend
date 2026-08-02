"""사용자 데이터의 영속성 접근을 담당하는 repository 모듈."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.users.models import User


class UserRepository:
    """User 모델에 대한 조회와 저장 연산을 제공한다."""

    @staticmethod
    def find_by_id(db: Session, user_id: int) -> User | None:
        """사용자 식별자로 사용자를 조회한다."""
        return db.scalar(select(User).where(User.user_id == user_id))

    @staticmethod
    def find_by_email(db: Session, email: str) -> User | None:
        """정규화된 이메일로 사용자를 조회한다."""
        return db.scalar(select(User).where(User.email == email))

    @staticmethod
    def find_by_nickname(db: Session, nickname: str) -> User | None:
        """정규화된 닉네임으로 사용자를 조회한다."""
        return db.scalar(select(User).where(User.nickname == nickname))

    @staticmethod
    def add(db: Session, user: User) -> User:
        """새 사용자를 session에 추가하고 식별자를 할당받는다."""
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def refresh(db: Session, user: User) -> User:
        """DB에 저장된 최신 사용자 상태를 다시 읽는다."""
        db.refresh(user)
        return user

    @staticmethod
    def update_email_verified_at(db: Session, user: User, verified_at: datetime) -> None:
        """사용자의 이메일 인증 완료 시각을 session에 반영한다."""
        user.email_verified_at = verified_at
        db.add(user)

    @staticmethod
    def update_last_login_at(db: Session, user: User, logged_in_at: datetime) -> None:
        """사용자의 마지막 로그인 시각을 session에 반영한다."""
        user.last_login_at = logged_in_at
        db.add(user)

    @staticmethod
    def update_password_hash(db: Session, user: User, password_hash: str) -> None:
        """사용자의 비밀번호 해시를 session에 반영한다."""
        user.password_hash = password_hash
        db.add(user)
