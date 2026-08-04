"""사용자 알림 생성, 조회 및 읽음 처리 데이터 접근 연산."""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domains.notifications.models import Notification


class NotificationRepository:
    """알림 생성 연산을 제공한다."""

    @staticmethod
    def find(db: Session, notification_id: int, *, lock: bool = False) -> Notification | None:
        query = select(Notification).where(Notification.notification_id == notification_id)
        if lock:
            query = query.with_for_update()
        return db.scalar(query)

    @staticmethod
    def page(
        db: Session,
        user_id: int,
        *,
        page: int,
        size: int,
        is_read: bool | None,
        notification_type: str | None,
    ) -> tuple[list[Notification], int]:
        """사용자 알림을 필터링하여 최신순 페이지로 조회한다."""
        query = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            query = query.where(Notification.is_read.is_(is_read))
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            db.scalars(
                query.order_by(Notification.created_at.desc(), Notification.notification_id.desc())
                .offset(page * size)
                .limit(size)
            ).all()
        )
        return items, total

    @staticmethod
    def unread_count(db: Session, user_id: int) -> int:
        return (
            db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            )
            or 0
        )

    @staticmethod
    def mark_all_read(db: Session, user_id: int, *, before: datetime, read_at: datetime) -> int:
        result = db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.created_at <= before,
            )
            .values(is_read=True, read_at=read_at)
            .execution_options(synchronize_session=False)
        )
        return result.rowcount or 0

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

    @staticmethod
    def find_equivalent(
        db: Session,
        *,
        user_id: int,
        notification_type: str,
        reference_type: str,
        reference_id: int,
        content: str,
    ) -> Notification | None:
        """동일 도메인 이벤트가 이미 생성한 알림을 조회한다."""
        return db.scalar(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.notification_type == notification_type,
                Notification.reference_type == reference_type,
                Notification.reference_id == reference_id,
                Notification.content == content,
            )
        )
