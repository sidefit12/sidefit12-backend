"""S3 호환 오브젝트 스토리지 연동 모듈."""

from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings


class ObjectStorage(Protocol):
    """파일 서비스가 사용하는 오브젝트 스토리지 계약."""

    def upload(self, key: str, content: bytes, content_type: str) -> None: ...

    def delete(self, key: str) -> None: ...

    def url(self, key: str, *, public: bool) -> str: ...


class S3ObjectStorage:
    """AWS S3와 S3 호환 저장소에 파일을 저장한다."""

    def __init__(self) -> None:
        settings = get_settings()
        if not all(
            (
                settings.storage_access_key,
                settings.storage_secret_key,
                settings.storage_bucket,
            )
        ):
            raise RuntimeError("오브젝트 스토리지 설정이 필요합니다.")
        import boto3

        self.bucket = settings.storage_bucket
        self.public_base_url = settings.storage_public_base_url
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.storage_endpoint_url,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            region_name=settings.storage_region,
        )

    def upload(self, key: str, content: bytes, content_type: str) -> None:
        """파일 바이트를 지정한 객체 키로 업로드한다."""
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content, ContentType=content_type)

    def delete(self, key: str) -> None:
        """저장소에서 객체를 삭제한다."""
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def url(self, key: str, *, public: bool) -> str:
        """공개 URL 또는 제한 시간 서명 URL을 반환한다."""
        if public and self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{key}"
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600,
        )


class UnavailableObjectStorage:
    """설정 또는 드라이버가 준비되지 않았을 때 명시적으로 실패하는 저장소."""

    def upload(self, key: str, content: bytes, content_type: str) -> None:
        raise RuntimeError("오브젝트 스토리지를 사용할 수 없습니다.")

    def delete(self, key: str) -> None:
        raise RuntimeError("오브젝트 스토리지를 사용할 수 없습니다.")

    def url(self, key: str, *, public: bool) -> str:
        raise RuntimeError("오브젝트 스토리지를 사용할 수 없습니다.")


@lru_cache
def get_object_storage() -> ObjectStorage:
    """설정에 연결된 S3 호환 저장소를 반환한다."""
    try:
        return S3ObjectStorage()
    except (ImportError, RuntimeError):
        return UnavailableObjectStorage()
