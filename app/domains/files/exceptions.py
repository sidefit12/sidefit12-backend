"""파일 도메인 예외."""

from fastapi import status

from app.core.exceptions import AppException


class FileNotFoundError(AppException):
    def __init__(self, file_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="FILE_NOT_FOUND",
            message="파일을 찾을 수 없습니다.",
            details={"fileId": file_id},
        )


class FileOwnershipRequiredError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="RESOURCE_OWNERSHIP_REQUIRED",
            message="리소스 소유자만 처리할 수 있습니다.",
        )


class FileTooLargeError(AppException):
    def __init__(self, maximum: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message="파일 용량이 허용 범위를 초과했습니다.",
            details={"maximumBytes": maximum},
        )


class UnsupportedFileTypeError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="UNSUPPORTED_MEDIA_TYPE",
            message="지원하지 않는 파일 형식입니다.",
        )


class InvalidDownloadPolicyError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_DOWNLOAD_POLICY",
            message="공개 파일만 다운로드를 허용할 수 있습니다.",
        )


class StorageUnavailableError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="STORAGE_UNAVAILABLE",
            message="파일 저장 서비스를 일시적으로 사용할 수 없습니다.",
        )


class IdempotencyConflictError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message="동일한 멱등 키에 다른 요청을 사용할 수 없습니다.",
        )
