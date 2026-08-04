"""사용자 푸시 기기 데이터 접근 모듈."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domains.push_devices.models import PushDevice


class PushDeviceRepository:
    @staticmethod
    def find_by_token(db: Session, token: str) -> PushDevice | None:
        return db.scalar(select(PushDevice).where(PushDevice.registration_token == token))

    @staticmethod
    def active_tokens(db: Session, user_id: int) -> list[str]:
        return list(
            db.scalars(
                select(PushDevice.registration_token).where(
                    PushDevice.user_id == user_id, PushDevice.is_active.is_(True)
                )
            ).all()
        )

    @staticmethod
    def add(db: Session, device: PushDevice) -> PushDevice:
        db.add(device)
        db.flush()
        return device

    @staticmethod
    def deactivate_tokens(db: Session, tokens: set[str]) -> None:
        if tokens:
            db.execute(
                update(PushDevice)
                .where(PushDevice.registration_token.in_(tokens))
                .values(is_active=False)
            )
