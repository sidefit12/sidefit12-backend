"""프로젝트 지원 API 엔드포인트."""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Header, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.project_applications.openapi import (
    ACCEPT_REQUEST_EXAMPLE,
    APPLICATION_RESPONSE_EXAMPLE,
    CANCEL_REQUEST_EXAMPLE,
    CREATE_REQUEST_EXAMPLE,
    DECISION_RESPONSE_EXAMPLE,
    DETAIL_RESPONSE_EXAMPLE,
    PAGE_RESPONSE_EXAMPLE,
    REJECT_REQUEST_EXAMPLE,
    error_example,
    response_example,
)
from app.domains.project_applications.schemas import (
    ApplicationAcceptRequest,
    ApplicationCancelRequest,
    ApplicationCreateRequest,
    ApplicationDecisionResponse,
    ApplicationDetailResponse,
    ApplicationPageResponse,
    ApplicationRejectRequest,
    ApplicationResponse,
)
from app.domains.project_applications.service import ProjectApplicationService
from app.domains.users.models import User

router = APIRouter(tags=["프로젝트 지원"])
ApplicationStatus = Literal["PENDING", "ACCEPTED", "REJECTED", "CANCELED"]
AUTH_ERROR = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")


def _request_id():
    return request_id_context.get()


@router.post(
    "/projects/{projectId}/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="프로젝트 지원",
    description="모집 포지션과 지원 메시지로 대기 상태의 지원을 생성합니다.",
    operation_id="APP_001",
    responses={
        201: response_example("프로젝트 지원 성공", APPLICATION_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
        409: error_example("지원 상태 충돌", "ALREADY_APPLIED", "이미 지원한 프로젝트입니다."),
    },
)
def create_application(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    request: ApplicationCreateRequest = Body(
        openapi_examples={"default": {"summary": "지원 요청 예시", "value": CREATE_REQUEST_EXAMPLE}}
    ),
    idempotency_key: str | None = Header(
        None, alias="Idempotency-Key", description="지원 생성 멱등 키"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectApplicationService.create(
        db, user, project_id, request, idempotency_key=idempotency_key
    )
    return {"success": True, "data": data, "requestId": _request_id()}


@router.get(
    "/users/me/applications",
    response_model=ApplicationPageResponse,
    summary="내 지원 목록 조회",
    description="현재 사용자의 지원 목록과 상태별 개수를 반환합니다.",
    operation_id="APP_002",
    responses={
        200: response_example("내 지원 목록 조회 성공", PAGE_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
    },
)
def list_my_applications(
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    application_status: ApplicationStatus | None = Query(
        None, alias="status", description="지원 상태 필터"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectApplicationService.my_page(
        db, user, page=page, size=size, status=application_status
    )
    return {"success": True, "data": data, "meta": meta, "requestId": _request_id()}


@router.patch(
    "/applications/{applicationId}/cancel",
    response_model=ApplicationResponse,
    summary="지원 취소",
    description="지원자 본인의 대기 지원을 취소 상태로 변경합니다.",
    operation_id="APP_003",
    responses={
        200: response_example("지원 취소 성공", APPLICATION_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
        404: error_example("지원 없음", "APPLICATION_NOT_FOUND", "지원 내역을 찾을 수 없습니다."),
    },
)
def cancel_application(
    application_id: int = Path(alias="applicationId", gt=0, description="지원 식별자"),
    request: ApplicationCancelRequest = Body(
        openapi_examples={"default": {"summary": "지원 취소 예시", "value": CANCEL_REQUEST_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectApplicationService.cancel(db, user, application_id, request.reason)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.get(
    "/projects/{projectId}/applications",
    response_model=ApplicationPageResponse,
    summary="프로젝트 지원자 목록 조회",
    description="프로젝트 작성자가 포지션과 상태별 지원자 목록 및 집계를 조회합니다.",
    operation_id="APP_004",
    responses={
        200: response_example("지원자 목록 조회 성공", PAGE_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
        403: error_example(
            "소유자 권한 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
    },
)
def list_project_applications(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    application_status: ApplicationStatus | None = Query(
        None, alias="status", description="지원 상태 필터"
    ),
    position_id: int | None = Query(
        None, alias="projectPositionId", gt=0, description="모집 포지션 식별자 필터"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectApplicationService.project_page(
        db,
        user,
        project_id,
        page=page,
        size=size,
        status=application_status,
        position_id=position_id,
    )
    return {"success": True, "data": data, "meta": meta, "requestId": _request_id()}


@router.get(
    "/applications/{applicationId}",
    response_model=ApplicationDetailResponse,
    summary="지원자 상세 조회",
    description="지원 내용과 지원자의 현재 공개 프로필을 조회합니다.",
    operation_id="APP_005",
    responses={
        200: response_example("지원 상세 조회 성공", DETAIL_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
        404: error_example("지원 없음", "APPLICATION_NOT_FOUND", "지원 내역을 찾을 수 없습니다."),
    },
)
def get_application(
    application_id: int = Path(alias="applicationId", gt=0, description="지원 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectApplicationService.detail(db, user, application_id)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/applications/{applicationId}/accept",
    response_model=ApplicationDecisionResponse,
    summary="지원 승인",
    description="대기 지원을 승인하고 프로젝트 팀원을 생성합니다.",
    operation_id="APP_006",
    responses={
        200: response_example("지원 승인 성공", DECISION_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
        409: error_example(
            "모집 정원 초과", "POSITION_CAPACITY_EXCEEDED", "모집 정원이 모두 찼습니다."
        ),
    },
)
def accept_application(
    application_id: int = Path(alias="applicationId", gt=0, description="지원 식별자"),
    request: ApplicationAcceptRequest = Body(
        openapi_examples={"default": {"summary": "지원 승인 예시", "value": ACCEPT_REQUEST_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectApplicationService.accept(db, user, application_id, request.note)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/applications/{applicationId}/reject",
    response_model=ApplicationDecisionResponse,
    summary="지원 거절",
    description="대기 지원을 거절하고 거절 사유를 저장합니다.",
    operation_id="APP_007",
    responses={
        200: response_example("지원 거절 성공", DECISION_RESPONSE_EXAMPLE),
        401: AUTH_ERROR,
        409: error_example(
            "이미 처리된 지원", "APPLICATION_ALREADY_PROCESSED", "이미 처리된 지원입니다."
        ),
    },
)
def reject_application(
    application_id: int = Path(alias="applicationId", gt=0, description="지원 식별자"),
    request: ApplicationRejectRequest = Body(
        openapi_examples={"default": {"summary": "지원 거절 예시", "value": REJECT_REQUEST_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectApplicationService.reject(db, user, application_id, request)
    return {"success": True, "data": data, "requestId": _request_id()}
