"""파일 업로드와 삭제 비즈니스 로직."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.files.exceptions import (
    FileNotFoundError,
    FileOwnershipRequiredError,
    FileTooLargeError,
    IdempotencyConflictError,
    InvalidDownloadPolicyError,
    StorageUnavailableError,
    UnsupportedFileTypeError,
)
from app.domains.files.models import File
from app.domains.files.repository import FileRepository
from app.domains.files.schemas import FileData, FileResource
from app.domains.idempotency_requests.service import IdempotencyRequestService
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User
from app.integrations.object_storage import ObjectStorage


class FileService:
    """FILE-001~002의 파일 검증과 상태 변경을 처리한다."""

    RULES = {
        "PROFILE_IMAGE": {
            "maximum": 5 * 1024 * 1024,
            "extensions": {".jpg", ".jpeg", ".png", ".webp"},
            "mime_types": {"image/jpeg", "image/png", "image/webp"},
        },
        "PUBLIC_MATERIAL": {
            "maximum": 10 * 1024 * 1024,
            "extensions": {".pdf", ".jpg", ".jpeg", ".png", ".webp"},
            "mime_types": {"application/pdf", "image/jpeg", "image/png", "image/webp"},
        },
    }

    @staticmethod
    def upload(
        db: Session,
        user: User,
        storage: ObjectStorage,
        *,
        filename: str,
        declared_mime_type: str,
        content: bytes,
        file_category: str,
        visibility: str,
        preview_allowed: bool,
        download_allowed: bool,
        idempotency_key: str | None,
    ) -> FileData:
        """파일을 검증한 뒤 저장소와 DB에 원자적으로 등록한다."""
        if download_allowed and visibility != "PUBLIC":
            raise InvalidDownloadPolicyError()
        mime_type = FileService._validate(filename, declared_mime_type, content, file_category)
        request_hash = FileService._request_hash(
            filename,
            content,
            file_category,
            visibility,
            preview_allowed,
            download_allowed,
        )
        if idempotency_key:
            existing = IdempotencyRequestService.find(db, user.user_id, idempotency_key)
            if existing:
                if existing.request_hash != request_hash:
                    raise IdempotencyConflictError()
                file = FileRepository.find(db, existing.resource_id)
                if file is not None and file.file_status == "ACTIVE":
                    return FileService._data(file, storage)

        extension = Path(filename).suffix.lower()
        storage_key = f"users/{user.user_id}/{file_category.lower()}/{uuid4().hex}{extension}"
        try:
            storage.upload(storage_key, content, mime_type)
        except Exception as exc:
            raise StorageUnavailableError() from exc

        try:
            file = FileRepository.add(
                db,
                File(
                    uploader_user_id=user.user_id,
                    storage_key=storage_key,
                    original_name=Path(filename).name,
                    mime_type=mime_type,
                    file_size=len(content),
                    file_category=file_category,
                    visibility=visibility,
                    preview_allowed=preview_allowed,
                    download_allowed=download_allowed,
                    file_status="ACTIVE",
                ),
            )
            if idempotency_key:
                IdempotencyRequestService.add(
                    db, user.user_id, idempotency_key, request_hash, file.file_id
                )
            db.commit()
        except Exception:
            db.rollback()
            try:
                storage.delete(storage_key)
            except Exception:
                pass
            raise
        return FileService._data(file, storage)

    @staticmethod
    def delete(db: Session, user: User, storage: ObjectStorage, file_id: int) -> None:
        """소유 파일의 프로필 참조를 해제하고 소프트 삭제한다."""
        file = FileRepository.find(db, file_id)
        if file is None:
            raise FileNotFoundError(file_id)
        if file.uploader_user_id != user.user_id:
            raise FileOwnershipRequiredError()
        if file.file_status == "DELETED":
            return
        ProfileService.detach_file_references(db, file_id)
        FileRepository.mark_deleted(file, datetime.now(timezone.utc))
        db.commit()
        try:
            storage.delete(file.storage_key)
        except Exception:
            # DB의 삭제 상태가 원본이며 저장소 정리는 재시도 가능한 후속 작업이다.
            pass

    @staticmethod
    def validate_profile_reference(
        db: Session, user_id: int, file_id: int, expected_category: str
    ) -> File:
        """프로필 도메인에 활성 파일의 소유권과 분류 검증을 제공한다."""
        file = FileRepository.find(db, file_id)
        if file is None or file.file_status != "ACTIVE":
            raise FileNotFoundError(file_id)
        if file.uploader_user_id != user_id:
            raise FileOwnershipRequiredError()
        if file.file_category != expected_category:
            raise UnsupportedFileTypeError()
        return file

    @staticmethod
    def _validate(filename: str, mime_type: str, content: bytes, category: str) -> str:
        rule = FileService.RULES.get(category)
        if rule is None:
            raise UnsupportedFileTypeError()
        if len(content) > rule["maximum"]:
            raise FileTooLargeError(rule["maximum"])
        extension = Path(filename).suffix.lower()
        detected = FileService._detect_mime_type(content)
        if (
            not content
            or extension not in rule["extensions"]
            or mime_type not in rule["mime_types"]
            or detected != mime_type
        ):
            raise UnsupportedFileTypeError()
        return detected

    @staticmethod
    def _detect_mime_type(content: bytes) -> str | None:
        if content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
            return "image/webp"
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        return None

    @staticmethod
    def _request_hash(
        filename: str,
        content: bytes,
        category: str,
        visibility: str,
        preview_allowed: bool,
        download_allowed: bool,
    ) -> str:
        digest = hashlib.sha256(content).hexdigest()
        value = "|".join(
            (
                Path(filename).name,
                digest,
                category,
                visibility,
                str(preview_allowed),
                str(download_allowed),
            )
        )
        return hashlib.sha256(value.encode()).hexdigest()

    @staticmethod
    def _data(file: File, storage: ObjectStorage) -> FileData:
        try:
            url = storage.url(file.storage_key, public=file.visibility == "PUBLIC")
        except Exception as exc:
            raise StorageUnavailableError() from exc
        return FileData(
            file=FileResource(
                file_id=file.file_id,
                original_name=file.original_name,
                mime_type=file.mime_type,
                file_size=file.file_size,
                file_category=file.file_category,
                visibility=file.visibility,
                preview_allowed=file.preview_allowed,
                download_allowed=file.download_allowed,
                url=url,
                created_at=file.created_at,
            )
        )
