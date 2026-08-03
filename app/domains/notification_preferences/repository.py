"""사용자 알림 수신 설정 데이터 접근 연산."""

from sqlalchemy.orm import Session

from app.domains.notification_preferences.models import NotificationPreference


class NotificationPreferenceRepository:
    """알림 설정 조회와 생성을 담당한다."""

    @staticmethod
    def find(db: Session, user_id: int) -> NotificationPreference | None:
        return db.get(NotificationPreference, user_id)

    @staticmethod
    def add(db: Session, user_id: int) -> NotificationPreference:
        preference = NotificationPreference(user_id=user_id)
        db.add(preference)
        db.flush()
        return preference
