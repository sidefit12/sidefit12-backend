"""사용자 신고 API 라우터."""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.reports.openapi import ONE, error_example, response_example
from app.domains.reports.schemas import ReportCreateRequest, ReportResponse
from app.domains.reports.service import ReportService
from app.domains.users.models import User

router = APIRouter(tags=["신고"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")


@router.post(
    "/projects/{projectId}/reports",
    response_model=ReportResponse,
    status_code=201,
    summary="프로젝트 신고",
    description="프로젝트를 사유와 상세 내용으로 신고합니다.",
    operation_id="REPORT_001",
    responses={
        201: response_example("프로젝트 신고 성공", ONE),
        401: AUTH,
        404: error_example("프로젝트 없음", "PROJECT_NOT_FOUND", "프로젝트를 찾을 수 없습니다."),
        409: error_example("신고 충돌", "DUPLICATE_REPORT", "이미 신고한 대상입니다."),
    },
)
def report_project(
    request: ReportCreateRequest,
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ReportService.report_project(db, user, project_id, request),
        "requestId": request_id_context.get(),
    }


@router.post(
    "/users/{userId}/reports",
    response_model=ReportResponse,
    status_code=201,
    summary="사용자 신고",
    description="사용자를 사유와 상세 내용으로 신고합니다.",
    operation_id="REPORT_002",
    responses={
        201: response_example("사용자 신고 성공", ONE),
        401: AUTH,
        404: error_example("사용자 없음", "USER_NOT_FOUND", "사용자를 찾을 수 없습니다."),
        409: error_example("신고 충돌", "DUPLICATE_REPORT", "이미 신고한 대상입니다."),
    },
)
def report_user(
    request: ReportCreateRequest,
    target_user_id: int = Path(alias="userId", ge=1, description="신고 대상 사용자 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ReportService.report_user(db, user, target_user_id, request),
        "requestId": request_id_context.get(),
    }
