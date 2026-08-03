"""멱등 요청 서비스."""

from sqlalchemy.orm import Session

from app.domains.idempotency_requests.repository import IdempotencyRequestRepository


class IdempotencyRequestService:
    @staticmethod
    def find(db: Session, user_id: int, key: str):
        return IdempotencyRequestRepository.find(db, user_id, key)

    @staticmethod
    def add(db: Session, user_id: int, key: str, request_hash: str, resource_id: int) -> None:
        IdempotencyRequestRepository.add(db, user_id, key, request_hash, resource_id)
