"""프로젝트 API 명세의 HTTP 엔드포인트."""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Header, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user, get_optional_current_user
from app.domains.projects.openapi import (
    CREATE_EXAMPLE,
    DETAIL_EXAMPLE,
    PAGE_EXAMPLE,
    STATUS_EXAMPLE,
    UPDATE_EXAMPLE,
)
from app.domains.projects.openapi import (
    error_example as _error,
)
from app.domains.projects.openapi import (
    response_example as _response,
)
from app.domains.projects.schemas import (
    ProjectCreateRequest,
    ProjectDeleteRequest,
    ProjectDetailResponse,
    ProjectPageResponse,
    ProjectStatusRequest,
    ProjectStatusResponse,
    ProjectUpdateRequest,
    RecruitmentStatusRequest,
)
from app.domains.projects.service import ProjectService
from app.domains.users.models import User

router = APIRouter(tags=["프로젝트"])
AUTH = {"description": "로그인이 필요합니다."}
OWNER = {"description": "리소스 소유자만 처리할 수 있습니다."}
NOT_FOUND = {"description": "프로젝트를 찾을 수 없습니다."}


def _ids(value: str | None, maximum: int) -> list[int] | None:
    """쉼표로 구분된 양의 식별자 목록을 변환한다."""
    if value is None or not value.strip():
        return None
    try:
        result = [int(x.strip()) for x in value.split(",")]
    except ValueError as exc:
        raise ValueError("식별자 목록이 올바르지 않습니다.") from exc
    if len(result) > maximum or any(x <= 0 for x in result):
        raise ValueError("식별자 목록이 올바르지 않습니다.")
    return result


@router.get(
    "/projects",
    response_model=ProjectPageResponse,
    summary="프로젝트 목록·검색 조회",
    description="키워드·토픽·기술·역할·진행 방식·상태·정렬을 적용해 공개 프로젝트 목록을 반환합니다.",
    operation_id="PROJECT_001_list",
    responses={
        200: _response("프로젝트 목록·검색 조회 성공", PAGE_EXAMPLE),
        400: _error(
            "잘못된 조회 조건", "INVALID_QUERY_PARAMETER", "조회 조건이 올바르지 않습니다."
        ),
        404: _error("유효하지 않은 기준정보", "TOPIC_NOT_FOUND", "유효하지 않은 토픽입니다."),
    },
)
def list_projects(
    keyword: str | None = Query(
        None, min_length=2, max_length=50, description="제목과 요약에서 검색할 문자열"
    ),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    project_status: Literal["PREPARING", "IN_PROGRESS", "COMPLETED", "CANCELED"] | None = Query(
        None, alias="projectStatus", description="프로젝트 진행 상태"
    ),
    recruitment_status: Literal["DRAFT", "RECRUITING", "CLOSED"] = Query(
        "RECRUITING", alias="recruitmentStatus", description="프로젝트 모집 상태"
    ),
    role_ids: str | None = Query(
        None, alias="roleIds", description="쉼표로 구분한 역할 식별자 목록"
    ),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    sort: Literal["LATEST", "DEADLINE", "RECOMMENDED"] = Query(
        "LATEST", description="프로젝트 정렬 방식"
    ),
    tech_stack_ids: str | None = Query(
        None, alias="techStackIds", description="쉼표로 구분한 기술 스택 식별자 목록"
    ),
    topic_ids: str | None = Query(
        None, alias="topicIds", description="쉼표로 구분한 토픽 식별자 목록"
    ),
    work_type: Literal["ONLINE", "OFFLINE", "HYBRID"] | None = Query(
        None, alias="workType", description="프로젝트 진행 방식"
    ),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectService.page(
        db,
        viewer=user,
        page=page,
        size=size,
        project_status=project_status,
        recruitment_status=recruitment_status,
        work_type=work_type,
        topic_ids=_ids(topic_ids, 10),
        tech_stack_ids=_ids(tech_stack_ids, 20),
        role_ids=_ids(role_ids, 10),
        keyword=keyword,
        sort=sort,
        owner_user_id=None,
        include_deleted=False,
    )
    return {"data": data, "meta": meta, "requestId": request_id_context.get()}


@router.post(
    "/projects",
    response_model=ProjectDetailResponse,
    status_code=201,
    summary="프로젝트 모집글 작성",
    description="프로젝트·토픽·기술·포지션과 OWNER 팀원을 하나의 트랜잭션으로 생성합니다.",
    operation_id="PROJECT_002_create",
    responses={
        201: _response("프로젝트 모집글 작성 성공", DETAIL_EXAMPLE),
        400: _error("잘못된 입력값", "VALIDATION_ERROR", "입력값을 확인해 주세요."),
        401: _error("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다."),
        404: _error("유효하지 않은 기준정보", "ROLE_NOT_FOUND", "유효하지 않은 역할입니다."),
    },
)
def create_project(
    request: ProjectCreateRequest = Body(
        ...,
        openapi_examples={
            "default": {"summary": "프로젝트 모집글 작성 예시", "value": CREATE_EXAMPLE}
        },
    ),
    _idempotency_key: str | None = Header(
        None, alias="Idempotency-Key", description="프로젝트 중복 생성을 방지하는 멱등 키"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "data": ProjectService.create(db, user, request, _idempotency_key),
        "requestId": request_id_context.get(),
    }


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDetailResponse,
    summary="프로젝트 상세 조회",
    description="프로젝트·작성자·포지션·충원 현황과 로그인 사용자의 상태를 반환합니다.",
    operation_id="PROJECT_003_detail",
    responses={
        200: _response("프로젝트 상세 조회 성공", DETAIL_EXAMPLE),
        404: _error("프로젝트 없음", "PROJECT_NOT_FOUND", "프로젝트를 찾을 수 없습니다."),
    },
)
def get_project(
    project_id: int = Path(gt=0, description="조회할 프로젝트 식별자"),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    return {
        "data": ProjectService.detail(db, project_id, user),
        "requestId": request_id_context.get(),
    }


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectDetailResponse,
    summary="프로젝트 모집글 수정",
    description="작성자가 프로젝트와 모집 조건을 부분 수정합니다.",
    operation_id="PROJECT_004_update",
    responses={
        200: _response("프로젝트 모집글 수정 성공", DETAIL_EXAMPLE),
        400: _error("잘못된 입력값", "VALIDATION_ERROR", "입력값을 확인해 주세요."),
        401: _error("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다."),
        403: _error(
            "소유권 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
        409: _error("모집 정원 초과", "POSITION_CAPACITY_EXCEEDED", "모집 정원이 모두 찼습니다."),
    },
)
def update_project(
    request: ProjectUpdateRequest = Body(
        ...,
        openapi_examples={
            "default": {"summary": "프로젝트 모집글 수정 예시", "value": UPDATE_EXAMPLE}
        },
    ),
    project_id: int = Path(gt=0, description="수정할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "data": ProjectService.update(db, user, project_id, request),
        "requestId": request_id_context.get(),
    }


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="프로젝트 모집글 삭제",
    description="모집글을 소프트 삭제하며 이미 삭제된 요청은 성공으로 처리합니다.",
    operation_id="PROJECT_005_delete",
    responses={
        401: _error("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다."),
        403: _error(
            "소유권 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
        409: _error(
            "삭제 불가",
            "CANNOT_DELETE_PROJECT_WITH_MEMBERS",
            "확정 팀원이 있어 삭제할 수 없습니다.",
        ),
    },
)
def delete_project(
    request: ProjectDeleteRequest = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "프로젝트 삭제 예시",
                "value": {"deletionReason": "프로젝트 계획 변경으로 모집을 종료합니다."},
            }
        },
    ),
    project_id: int = Path(gt=0, description="삭제할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectService.delete(db, user, project_id, request.deletion_reason)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/projects/{project_id}/recruitment-status",
    response_model=ProjectStatusResponse,
    summary="모집 상태 변경",
    description="프로젝트 모집을 시작·종료·재개합니다.",
    operation_id="PROJECT_006_recruitment_status",
    responses={
        200: _response("모집 상태 변경 성공", STATUS_EXAMPLE),
        400: _error(
            "잘못된 상태 전이",
            "INVALID_STATE_TRANSITION",
            "현재 상태에서는 요청을 처리할 수 없습니다.",
        ),
        401: _error("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다."),
        403: _error(
            "소유권 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
        409: _error("마감일 경과", "RECRUITMENT_DEADLINE_PASSED", "모집 마감일이 지났습니다."),
    },
)
def change_recruitment_status(
    request: RecruitmentStatusRequest = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "모집 상태 변경 예시",
                "value": {"recruitmentStatus": "CLOSED", "newDeadline": "2026-09-10T14:59:59Z"},
            }
        },
    ),
    project_id: int = Path(gt=0, description="모집 상태를 변경할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "data": ProjectService.change_recruitment_status(db, user, project_id, request),
        "requestId": request_id_context.get(),
    }


@router.patch(
    "/projects/{project_id}/status",
    response_model=ProjectStatusResponse,
    summary="프로젝트 진행 상태 변경",
    description="프로젝트 진행 상태를 준비·진행·완료·취소로 변경합니다.",
    operation_id="PROJECT_007_status",
    responses={
        200: _response("프로젝트 진행 상태 변경 성공", STATUS_EXAMPLE),
        400: _error(
            "잘못된 상태 전이",
            "INVALID_STATE_TRANSITION",
            "현재 상태에서는 요청을 처리할 수 없습니다.",
        ),
        401: _error("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다."),
        403: _error(
            "소유권 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
    },
)
def change_project_status(
    request: ProjectStatusRequest = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "프로젝트 진행 상태 변경 예시",
                "value": {"projectStatus": "IN_PROGRESS", "reason": "프로젝트 개발을 시작합니다."},
            }
        },
    ),
    project_id: int = Path(gt=0, description="진행 상태를 변경할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "data": ProjectService.change_project_status(db, user, project_id, request),
        "requestId": request_id_context.get(),
    }


@router.get(
    "/users/me/projects",
    response_model=ProjectPageResponse,
    summary="내 모집글 목록 조회",
    description="사용자가 작성한 프로젝트와 충원 요약을 조회합니다.",
    operation_id="PROJECT_009_my_projects",
    responses={
        200: _response("내 모집글 목록 조회 성공", PAGE_EXAMPLE),
        400: _error(
            "잘못된 조회 조건", "INVALID_QUERY_PARAMETER", "조회 조건이 올바르지 않습니다."
        ),
        401: _error("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다."),
    },
)
def my_projects(
    include_deleted: bool = Query(
        False, alias="includeDeleted", description="삭제된 프로젝트 포함 여부"
    ),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    recruitment_status: Literal["DRAFT", "RECRUITING", "CLOSED"] | None = Query(
        None, alias="status", description="프로젝트 모집 상태"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectService.my_page(
        db,
        user,
        page=page,
        size=size,
        project_status=None,
        recruitment_status=recruitment_status,
        work_type=None,
        topic_ids=None,
        tech_stack_ids=None,
        role_ids=None,
        keyword=None,
        sort="LATEST",
        include_deleted=include_deleted,
    )
    return {"data": data, "meta": meta, "requestId": request_id_context.get()}
