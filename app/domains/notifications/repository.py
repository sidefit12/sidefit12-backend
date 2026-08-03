"""사용자 알림 데이터 접근 연산."""

from sqlalchemy.orm import Session

from app.domains.notifications.models import Notification


class NotificationRepository:
    """알림 생성 연산을 제공한다."""

    @staticmethod
    def add(
        db: Session,
        *,
        user_id: int,
        notification_type: str,
        title: str,
        content: str,
        reference_type: str,
        reference_id: int,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        db.add(notification)
        return notification
