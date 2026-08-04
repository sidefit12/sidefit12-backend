"""파일 메타데이터 repository."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domains.files.models import File


class FileRepository:
    """파일 메타데이터의 영속성을 관리한다."""

    @staticmethod
    def find(db: Session, file_id: int) -> File | None:
        """식별자로 파일을 조회한다."""
        return db.get(File, file_id)

    @staticmethod
    def add(db: Session, file: File) -> File:
        """파일 메타데이터를 추가하고 식별자를 할당한다."""
        db.add(file)
        db.flush()
        return file

    @staticmethod
    def mark_deleted(file: File, deleted_at: datetime) -> None:
        """파일을 삭제 상태로 변경한다."""
        file.file_status = "DELETED"
        file.deleted_at = deleted_at
