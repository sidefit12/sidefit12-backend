"""사용자 조회, 생성 및 상태 변경 규칙을 담당하는 service 모듈."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.users.models import User
from app.domains.users.repository import UserRepository


class UserService:
    """다른 도메인에서도 사용할 수 있는 사용자 도메인 연산을 제공한다."""

    @staticmethod
    def normalize_email(email: str) -> str:
        """이메일의 앞뒤 공백을 제거하고 소문자로 정규화한다."""
        return email.strip().lower()

    @staticmethod
    def normalize_nickname(nickname: str) -> str:
        """닉네임의 앞뒤 공백을 제거한다."""
        return nickname.strip()

    @classmethod
    def get_by_id(cls, db: Session, user_id: int) -> User | None:
        """사용자 식별자로 사용자를 조회한다."""
        return UserRepository.find_by_id(db, user_id)

    @classmethod
    def get_by_email(cls, db: Session, email: str) -> User | None:
        """정규화된 이메일로 사용자를 조회한다."""
        return UserRepository.find_by_email(db, cls.normalize_email(email))

    @classmethod
    def get_by_nickname(cls, db: Session, nickname: str) -> User | None:
        """정규화된 닉네임으로 사용자를 조회한다."""
        return UserRepository.find_by_nickname(db, cls.normalize_nickname(nickname))

    @classmethod
    def create_active_user(
        cls,
        db: Session,
        *,
        email: str,
        password_hash: str,
        nickname: str,
    ) -> User:
        """이메일 인증을 마친 활성 사용자를 session에 생성한다."""
        user = User(
            email=cls.normalize_email(email),
            password_hash=password_hash,
            nickname=cls.normalize_nickname(nickname),
            user_status="ACTIVE",
        )
        return UserRepository.add(db, user)

    @staticmethod
    def mark_email_verified(db: Session, user: User, verified_at: datetime | None = None) -> None:
        """사용자의 이메일 인증 완료 시각을 변경한다."""
        UserRepository.update_email_verified_at(
            db,
            user,
            verified_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def update_last_login(db: Session, user: User, logged_in_at: datetime | None = None) -> None:
        """사용자의 마지막 로그인 시각을 변경한다."""
        UserRepository.update_last_login_at(
            db,
            user,
            logged_in_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def refresh(db: Session, user: User) -> User:
        """저장 완료된 사용자 데이터를 DB에서 다시 읽는다."""
        return UserRepository.refresh(db, user)

    @staticmethod
    def update_password_hash(db: Session, user: User, password_hash: str) -> None:
        """검증이 끝난 새 비밀번호 해시를 사용자 데이터에 반영한다."""
        UserRepository.update_password_hash(db, user, password_hash)
