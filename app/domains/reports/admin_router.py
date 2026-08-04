"""관리자 신고 처리 API 라우터."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.reports.openapi import DETAIL, PAGE, error_example, response_example
from app.domains.reports.schemas import (
    AdminReportDetailResponse,
    AdminReportRequest,
    ReportPageResponse,
)
from app.domains.reports.service import ReportService
from app.domains.users.models import User

router = APIRouter(tags=["관리자"])
ADMIN = error_example("관리자 권한 필요", "ADMIN_ROLE_REQUIRED", "관리자 권한이 필요합니다.")


@router.get(
    "/admin/reports",
    response_model=ReportPageResponse,
    summary="관리자 신고 목록 조회",
    description="관리자가 상태·대상 유형·기간 조건으로 신고를 조회합니다.",
    operation_id="ADMIN_001",
    responses={200: response_example("신고 목록 조회 성공", PAGE), 403: ADMIN},
)
def list_reports(
    from_at: datetime | None = Query(None, alias="from", description="조회 시작 일시"),
    to_at: datetime | None = Query(None, alias="to", description="조회 종료 일시"),
    report_status: Literal["PENDING", "IN_REVIEW", "RESOLVED", "REJECTED"] | None = Query(
        None, alias="status", description="신고 처리 상태"
    ),
    target_type: Literal["USER", "PROJECT"] | None = Query(
        None, alias="targetType", description="신고 대상 유형"
    ),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ReportService.admin_page(
        db,
        user,
        page=page,
        size=size,
        status=report_status,
        target_type=target_type,
        from_at=from_at,
        to_at=to_at,
    )
    return {"success": True, "data": data, "meta": meta, "requestId": request_id_context.get()}


@router.get(
    "/admin/reports/{reportId}",
    response_model=AdminReportDetailResponse,
    summary="관리자 신고 상세 조회",
    description="관리자가 신고 내용·대상·처리 정보를 조회합니다.",
    operation_id="ADMIN_002",
    responses={
        200: response_example("신고 상세 조회 성공", DETAIL),
        403: ADMIN,
        404: error_example("신고 없음", "REPORT_NOT_FOUND", "신고를 찾을 수 없습니다."),
    },
)
def report_detail(
    report_id: int = Path(alias="reportId", ge=1, description="신고 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ReportService.admin_detail(db, user, report_id),
        "requestId": request_id_context.get(),
    }


@router.patch(
    "/admin/reports/{reportId}",
    response_model=AdminReportDetailResponse,
    summary="관리자 신고 처리",
    description="신고 상태와 메모를 갱신하고 대상 숨김 또는 정지 조치를 수행합니다.",
    operation_id="ADMIN_003",
    responses={
        200: response_example("신고 처리 성공", DETAIL),
        403: ADMIN,
        404: error_example("신고 없음", "REPORT_NOT_FOUND", "신고를 찾을 수 없습니다."),
        409: error_example("처리 완료", "REPORT_ALREADY_PROCESSED", "이미 처리된 신고입니다."),
    },
)
def process_report(
    request: AdminReportRequest,
    report_id: int = Path(alias="reportId", ge=1, description="신고 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ReportService.process(db, user, report_id, request),
        "requestId": request_id_context.get(),
    }
