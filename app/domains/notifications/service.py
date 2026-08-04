"""사용자 알림 생성, 조회 및 읽음 처리 비즈니스 로직."""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.notification_preferences.service import NotificationPreferenceService
from app.domains.notifications.exceptions import (
    NotificationAccessDeniedError,
    NotificationNotFoundError,
)
from app.domains.notifications.repository import NotificationRepository
from app.domains.notifications.schemas import (
    NotificationPageData,
    NotificationResource,
    PageMeta,
    ReadAllNotificationsData,
)
from app.domains.users.models import User


class NotificationService:
    """NOTI-001~004와 다른 도메인의 업무 알림 생성을 제공한다."""

    @staticmethod
    def application_received(db: Session, owner_user_id: int, application_id: int) -> bool:
        if not NotificationPreferenceService.is_enabled(db, owner_user_id, "APPLICATION"):
            return False
        return NotificationService._add_once(
            db,
            user_id=owner_user_id,
            notification_type="APPLICATION_RECEIVED",
            title="새로운 프로젝트 지원이 도착했습니다.",
            content="프로젝트 지원자 정보를 확인해 주세요.",
            reference_type="APPLICATION",
            reference_id=application_id,
        )

    @staticmethod
    def application_decided(
        db: Session, applicant_user_id: int, application_id: int, *, accepted: bool
    ) -> bool:
        if not NotificationPreferenceService.is_enabled(db, applicant_user_id, "APPLICATION"):
            return False
        return NotificationService._add_once(
            db,
            user_id=applicant_user_id,
            notification_type="APPLICATION_ACCEPTED" if accepted else "APPLICATION_REJECTED",
            title="프로젝트 지원 결과가 도착했습니다.",
            content="지원이 승인되었습니다." if accepted else "지원이 거절되었습니다.",
            reference_type="APPLICATION",
            reference_id=application_id,
        )

    @staticmethod
    def team_member_changed(db: Session, user_id: int, project_id: int, *, event_type: str) -> bool:
        """확정 Enum을 사용해 팀원 이탈·복구 알림을 생성한다."""
        if not NotificationPreferenceService.is_enabled(db, user_id, "TEAM"):
            return False
        messages = {
            "LEFT": (
                "MEMBER_LEFT",
                "프로젝트 팀원이 탈퇴했습니다.",
                "팀원 변경 사항을 확인해 주세요.",
            ),
            "REMOVED": (
                "MEMBER_LEFT",
                "프로젝트 팀원 상태가 변경되었습니다.",
                "프로젝트에서 퇴출되었습니다.",
            ),
            "RESTORED": (
                "MEMBER_JOINED",
                "프로젝트 팀원으로 복구되었습니다.",
                "프로젝트에 다시 참여할 수 있습니다.",
            ),
        }
        notification_type, title, content = messages[event_type]
        return NotificationService._add_once(
            db,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            reference_type="PROJECT",
            reference_id=project_id,
        )

    @staticmethod
    def recruitment_closed(db: Session, owner_user_id: int, project_id: int) -> bool:
        """모집 자동 종료 알림을 수신 설정과 멱등 규칙에 따라 생성한다."""
        if not NotificationPreferenceService.is_enabled(db, owner_user_id, "RECRUITMENT_DEADLINE"):
            return False
        return NotificationService._add_once(
            db,
            user_id=owner_user_id,
            notification_type="RECRUITMENT_CLOSED",
            title="프로젝트 모집이 종료되었습니다.",
            content="마감일 경과 또는 포지션 충원으로 모집이 자동 종료되었습니다.",
            reference_type="PROJECT",
            reference_id=project_id,
        )

    @staticmethod
    def _add_once(
        db: Session,
        *,
        user_id: int,
        notification_type: str,
        title: str,
        content: str,
        reference_type: str,
        reference_id: int,
    ) -> bool:
        """동일 이벤트의 알림을 한 번만 생성한다."""
        existing = NotificationRepository.find_equivalent(
            db,
            user_id=user_id,
            notification_type=notification_type,
            reference_type=reference_type,
            reference_id=reference_id,
            content=content,
        )
        if existing is not None:
            return False
        NotificationRepository.add(
            db,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        return True

    @staticmethod
    def page(
        db: Session,
        user: User,
        *,
        page: int,
        size: int,
        is_read: bool | None,
        notification_type: str | None,
    ):
        items, total = NotificationRepository.page(
            db,
            user.user_id,
            page=page,
            size=size,
            is_read=is_read,
            notification_type=notification_type,
        )
        return NotificationPageData(
            items=[NotificationService._resource(item) for item in items],
            unread_count=NotificationRepository.unread_count(db, user.user_id),
        ), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )

    @staticmethod
    def unread_count(db: Session, user: User) -> int:
        return NotificationRepository.unread_count(db, user.user_id)

    @staticmethod
    def read(db: Session, user: User, notification_id: int) -> NotificationResource:
        notification = NotificationRepository.find(db, notification_id, lock=True)
        if notification is None:
            raise NotificationNotFoundError(notification_id)
        if notification.user_id != user.user_id:
            raise NotificationAccessDeniedError()
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            db.commit()
        return NotificationService._resource(notification)

    @staticmethod
    def read_all(db: Session, user: User, before: datetime | None) -> ReadAllNotificationsData:
        now = datetime.now(timezone.utc)
        boundary = before or now
        if boundary.tzinfo is None:
            boundary = boundary.replace(tzinfo=timezone.utc)
        updated = NotificationRepository.mark_all_read(
            db, user.user_id, before=boundary, read_at=now
        )
        db.commit()
        return ReadAllNotificationsData(
            updated_count=updated,
            unread_count=NotificationRepository.unread_count(db, user.user_id),
        )

    @staticmethod
    def _resource(notification) -> NotificationResource:
        return NotificationResource.model_validate(notification)
