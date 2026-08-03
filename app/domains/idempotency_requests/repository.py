"""멱등 요청 데이터 접근 연산."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.idempotency_requests.models import IdempotencyRequest


class IdempotencyRequestRepository:
    @staticmethod
    def find(db: Session, user_id: int, key: str):
        return db.scalar(
            select(IdempotencyRequest).where(
                IdempotencyRequest.user_id == user_id, IdempotencyRequest.idempotency_key == key
            )
        )

    @staticmethod
    def add(db: Session, user_id: int, key: str, request_hash: str, resource_id: int) -> None:
        db.add(
            IdempotencyRequest(
                user_id=user_id,
                idempotency_key=key,
                request_hash=request_hash,
                resource_id=resource_id,
            )
        )
