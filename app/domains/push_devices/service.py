"""푸시 기기 등록·삭제와 FCM 발송 서비스."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.push_devices.models import PushDevice
from app.domains.push_devices.repository import PushDeviceRepository
from app.domains.push_devices.schemas import PushDeviceData
from app.domains.users.models import User
from app.integrations.firebase_messaging import FirebaseMessagingService


class PushDeviceService:
    @staticmethod
    def register(db: Session, user: User, request) -> PushDeviceData:
        """FCM 토큰을 현재 사용자에게 멱등하게 등록한다."""
        device = PushDeviceRepository.find_by_token(db, request.registration_token)
        if device is None:
            device = PushDevice(
                user_id=user.user_id,
                registration_token=request.registration_token,
                platform=request.platform,
                device_name=request.device_name,
            )
            PushDeviceRepository.add(db, device)
        else:
            device.user_id = user.user_id
            device.platform = request.platform
            device.device_name = request.device_name
            device.is_active = True
            device.last_registered_at = datetime.now(timezone.utc)
        db.commit()
        return PushDeviceData(
            push_device_id=device.push_device_id,
            platform=device.platform,
            device_name=device.device_name,
            is_active=device.is_active,
        )

    @staticmethod
    def delete(db: Session, user: User, registration_token: str) -> bool:
        """현재 사용자가 소유한 FCM 토큰을 비활성화한다."""
        device = PushDeviceRepository.find_by_token(db, registration_token)
        if device is None or device.user_id != user.user_id or not device.is_active:
            return False
        device.is_active = False
        db.commit()
        return True

    @staticmethod
    def send_notification(
        db: Session,
        *,
        user_id: int,
        title: str,
        content: str,
        notification_type: str,
        reference_type: str,
        reference_id: int,
    ) -> int:
        """활성 기기에 알림을 발송하고 등록 해제된 토큰을 비활성화한다."""
        tokens = PushDeviceRepository.active_tokens(db, user_id)
        success_count, invalid_tokens = FirebaseMessagingService.send(
            tokens,
            title=title,
            body=content,
            data={
                "notificationType": notification_type,
                "referenceType": reference_type,
                "referenceId": str(reference_id),
            },
        )
        PushDeviceRepository.deactivate_tokens(db, invalid_tokens)
        return success_count
