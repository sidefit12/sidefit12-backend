"""프로젝트 팀원 API 엔드포인트."""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.project_members.openapi import (
    EVENT_PAGE_EXAMPLE,
    LEAVE_EXAMPLE,
    LIST_EXAMPLE,
    MEMBER_RESPONSE_EXAMPLE,
    REMOVE_EXAMPLE,
    RESTORE_EXAMPLE,
    error_example,
    response_example,
)
from app.domains.project_members.schemas import (
    MemberEventPageResponse,
    MemberLeaveRequest,
    MemberListResponse,
    MemberRemoveRequest,
    MemberResponse,
    MemberRestoreRequest,
)
from app.domains.project_members.service import ProjectMemberService
from app.domains.users.models import User

router = APIRouter(tags=["프로젝트 팀원"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")


def _request_id():
    return request_id_context.get()


@router.get(
    "/projects/{projectId}/members",
    response_model=MemberListResponse,
    summary="확정 팀원 목록 조회",
    description="팀원 목록과 포지션별 충원 현황을 반환하며 활성 팀원에게만 협업 채널을 제공합니다.",
    operation_id="MEMBER_001",
    responses={
        200: response_example("확정 팀원 목록 조회 성공", LIST_EXAMPLE),
        401: AUTH,
        404: error_example("프로젝트 없음", "PROJECT_NOT_FOUND", "프로젝트를 찾을 수 없습니다."),
    },
)
def list_members(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    include_channels: bool = Query(
        False, alias="includeChannels", description="활성 팀원에게만 허용되는 협업 채널 포함 여부"
    ),
    member_status: Literal["ACTIVE", "LEFT", "REMOVED"] | None = Query(
        "ACTIVE", alias="status", description="팀원 상태 필터"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectMemberService.list_members(
        db,
        user,
        project_id,
        status=member_status,
        include_channels=include_channels,
    )
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/projects/{projectId}/members/me/leave",
    response_model=MemberResponse,
    summary="프로젝트 자진 탈퇴",
    description="현재 사용자의 활성 팀원 상태를 탈퇴로 변경하고 이력을 기록합니다.",
    operation_id="MEMBER_002",
    responses={
        200: response_example("프로젝트 자진 탈퇴 성공", MEMBER_RESPONSE_EXAMPLE),
        401: AUTH,
        404: error_example("팀원 없음", "MEMBER_NOT_FOUND", "팀원을 찾을 수 없습니다."),
    },
)
def leave_project(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    request: MemberLeaveRequest = Body(
        openapi_examples={"default": {"summary": "탈퇴 요청 예시", "value": LEAVE_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectMemberService.leave(db, user, project_id, request.reason)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/projects/{projectId}/members/{memberId}/remove",
    response_model=MemberResponse,
    summary="프로젝트 팀원 퇴출",
    description="프로젝트 작성자가 팀원을 퇴출하고 10자 이상의 사유를 기록합니다.",
    operation_id="MEMBER_003",
    responses={
        200: response_example("프로젝트 팀원 퇴출 성공", MEMBER_RESPONSE_EXAMPLE),
        401: AUTH,
        403: error_example(
            "소유자 권한 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
    },
)
def remove_member(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    member_id: int = Path(alias="memberId", gt=0, description="프로젝트 팀원 식별자"),
    request: MemberRemoveRequest = Body(
        openapi_examples={"default": {"summary": "퇴출 요청 예시", "value": REMOVE_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectMemberService.remove(db, user, project_id, member_id, request.reason)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.patch(
    "/projects/{projectId}/members/{memberId}/restore",
    response_model=MemberResponse,
    summary="프로젝트 팀원 복구",
    description="프로젝트 작성자가 탈퇴 또는 퇴출 팀원을 모집 정원 내에서 복구합니다.",
    operation_id="MEMBER_004",
    responses={
        200: response_example("프로젝트 팀원 복구 성공", MEMBER_RESPONSE_EXAMPLE),
        401: AUTH,
        409: error_example(
            "모집 정원 초과", "POSITION_CAPACITY_EXCEEDED", "모집 정원이 모두 찼습니다."
        ),
    },
)
def restore_member(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    member_id: int = Path(alias="memberId", gt=0, description="프로젝트 팀원 식별자"),
    request: MemberRestoreRequest = Body(
        openapi_examples={"default": {"summary": "복구 요청 예시", "value": RESTORE_EXAMPLE}}
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectMemberService.restore(db, user, project_id, member_id, request.reason)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.get(
    "/projects/{projectId}/member-events",
    response_model=MemberEventPageResponse,
    summary="팀원 변경 이력 조회",
    description="활성 팀원에게 합류·탈퇴·퇴출·복구 이력을 최신순으로 반환합니다.",
    operation_id="MEMBER_005",
    responses={
        200: response_example("팀원 변경 이력 조회 성공", EVENT_PAGE_EXAMPLE),
        401: AUTH,
        403: error_example("접근 권한 없음", "ACCESS_DENIED", "접근 권한이 없습니다."),
    },
)
def list_member_events(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectMemberService.event_page(db, user, project_id, page=page, size=size)
    return {
        "success": True,
        "data": data,
        "meta": meta,
        "requestId": _request_id(),
    }
