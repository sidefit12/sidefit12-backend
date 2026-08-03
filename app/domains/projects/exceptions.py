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


class ResourceOwnershipRequiredError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=403,
            code="RESOURCE_OWNERSHIP_REQUIRED",
            message="리소스 소유자만 처리할 수 있습니다.",
        )


class ReferenceNotFoundError(AppException):
    def __init__(self, item_type: str, invalid_ids: list[int]) -> None:
        codes = {
            "topic": ("TOPIC_NOT_FOUND", "유효하지 않은 토픽입니다."),
            "techStack": ("TECH_STACK_NOT_FOUND", "유효하지 않은 기술 스택입니다."),
            "role": ("ROLE_NOT_FOUND", "유효하지 않은 역할입니다."),
        }
        code, message = codes[item_type]
        super().__init__(
            status_code=404, code=code, message=message, details={"invalid_ids": invalid_ids}
        )


class InvalidStateTransitionError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message="현재 상태에서는 요청을 처리할 수 없습니다.",
        )


class RecruitmentDeadlinePassedError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409, code="RECRUITMENT_DEADLINE_PASSED", message="모집 마감일이 지났습니다."
        )


class CannotDeleteProjectWithMembersError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            code="CANNOT_DELETE_PROJECT_WITH_MEMBERS",
            message="확정 팀원이 있어 삭제할 수 없습니다.",
        )


class IdempotencyConflictError(AppException):
    def __init__(self) -> None:
        super().__init__(
            status_code=409,
            code="IDEMPOTENCY_KEY_CONFLICT",
            message="동일한 멱등 키가 다른 요청에 사용되었습니다.",
        )
