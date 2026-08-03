"""다른 도메인에 알림 생성 기능을 제공하는 서비스."""

from sqlalchemy.orm import Session

from app.domains.notifications.repository import NotificationRepository


class NotificationService:
    """업무 이벤트에 따른 사용자 알림을 생성한다."""

    @staticmethod
    def application_received(db: Session, owner_user_id: int, application_id: int) -> None:
        NotificationRepository.add(
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
    ) -> None:
        NotificationRepository.add(
            db,
            user_id=applicant_user_id,
            notification_type="APPLICATION_ACCEPTED" if accepted else "APPLICATION_REJECTED",
            title="프로젝트 지원 결과가 도착했습니다.",
            content="지원이 승인되었습니다." if accepted else "지원이 거절되었습니다.",
            reference_type="APPLICATION",
            reference_id=application_id,
        )
