"""사용자 알림 수신 설정 조회와 수정 비즈니스 로직."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.notification_preferences.repository import NotificationPreferenceRepository
from app.domains.notification_preferences.schemas import NotificationPreferenceData
from app.domains.users.models import User


class NotificationPreferenceService:
    """NOTI-005~006과 알림 생성에 필요한 수신 설정을 제공한다."""

    @staticmethod
    def get(db: Session, user: User) -> NotificationPreferenceData:
        """저장된 설정 또는 DDL 기본값을 데이터 변경 없이 반환한다."""
        preference = NotificationPreferenceRepository.find(db, user.user_id)
        if preference is None:
            return NotificationPreferenceData(
                application_enabled=True,
                recruitment_deadline_enabled=True,
                team_enabled=True,
                system_enabled=True,
                updated_at=user.created_at,
            )
        return NotificationPreferenceData.model_validate(preference)

    @staticmethod
    def update(db: Session, user: User, request) -> NotificationPreferenceData:
        """사용자의 알림 설정을 부분 수정한다."""
        preference = NotificationPreferenceRepository.find(db, user.user_id)
        if preference is None:
            preference = NotificationPreferenceRepository.add(db, user.user_id)
        for field in request.model_fields_set:
            setattr(preference, field, getattr(request, field))
        preference.system_enabled = True
        preference.updated_at = datetime.now(timezone.utc)
        db.commit()
        return NotificationPreferenceData.model_validate(preference)

    @staticmethod
    def is_enabled(db: Session, user_id: int, category: str) -> bool:
        """알림 분류에 대한 사용자 수신 설정을 반환한다."""
        preference = NotificationPreferenceRepository.find(db, user_id)
        if preference is None:
            return True
        fields = {
            "APPLICATION": "application_enabled",
            "RECRUITMENT_DEADLINE": "recruitment_deadline_enabled",
            "TEAM": "team_enabled",
            "SYSTEM": "system_enabled",
        }
        return bool(getattr(preference, fields[category]))
