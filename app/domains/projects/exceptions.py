"""프로젝트 도메인 예외."""

from app.core.exceptions import AppException


class ProjectNotFoundError(AppException):
    def __init__(self, project_id: int) -> None:
        super().__init__(
            status_code=404,
            code="PROJECT_NOT_FOUND",
            message="프로젝트를 찾을 수 없습니다.",
            details={"project_id": project_id},
        )


class ProjectPermissionDeniedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=403,
            code="PROJECT_PERMISSION_DENIED",
            message="프로젝트를 변경할 권한이 없습니다.",
        )


class InvalidProjectSelectionError(AppException):
    def __init__(self, item_type: str, invalid_ids: list[int]) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_PROJECT_SELECTION",
            message="선택한 프로젝트 기준정보를 사용할 수 없습니다.",
            details={"item_type": item_type, "invalid_ids": invalid_ids},
        )


class InvalidProjectStateError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=409, code="INVALID_PROJECT_STATE", message=message)
