"""신고 및 관리자 처리 예외."""

from app.core.exceptions import AppException


class DuplicateReportError(AppException):
    def __init__(self):
        super().__init__(
            status_code=409, code="DUPLICATE_REPORT", message="이미 신고한 대상입니다."
        )


class CannotReportOwnResourceError(AppException):
    def __init__(self):
        super().__init__(
            status_code=409,
            code="CANNOT_REPORT_OWN_RESOURCE",
            message="본인이 작성한 프로젝트를 신고할 수 없습니다.",
        )


class CannotReportSelfError(AppException):
    def __init__(self):
        super().__init__(
            status_code=409, code="CANNOT_REPORT_SELF", message="본인을 신고할 수 없습니다."
        )


class ReportNotFoundError(AppException):
    def __init__(self):
        super().__init__(
            status_code=404, code="REPORT_NOT_FOUND", message="신고를 찾을 수 없습니다."
        )


class AdminRoleRequiredError(AppException):
    def __init__(self):
        super().__init__(
            status_code=403, code="ADMIN_ROLE_REQUIRED", message="관리자 권한이 필요합니다."
        )


class ReportAlreadyProcessedError(AppException):
    def __init__(self):
        super().__init__(
            status_code=409, code="REPORT_ALREADY_PROCESSED", message="이미 처리된 신고입니다."
        )


class ReportInvalidStateError(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            code="INVALID_STATE_TRANSITION",
            message="현재 상태에서는 요청을 처리할 수 없습니다.",
        )


class ReportUserNotFoundError(AppException):
    def __init__(self):
        super().__init__(
            status_code=404, code="USER_NOT_FOUND", message="사용자를 찾을 수 없습니다."
        )


class InvalidReportQueryError(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            code="INVALID_QUERY_PARAMETER",
            message="조회 조건이 올바르지 않습니다.",
        )
