"""프로젝트 모집 HTTP 엔드포인트."""

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.dependencies import get_current_user
from app.domains.projects.schemas import (
    ProjectCreateRequest,
    ProjectDeleteRequest,
    ProjectDeleteResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.domains.projects.service import ProjectService
from app.domains.users.models import User

router = APIRouter(prefix="/projects", tags=["프로젝트"])

AUTHENTICATION_REQUIRED = {"description": "로그인이 필요합니다."}
VALIDATION_ERROR = {"description": "요청값이 올바르지 않습니다."}
PROJECT_NOT_FOUND = {"description": "프로젝트를 찾을 수 없습니다."}
PROJECT_PERMISSION_DENIED = {"description": "프로젝트를 변경할 권한이 없습니다."}
INVALID_PROJECT_SELECTION = {
    "description": "선택한 토픽, 기술 스택 또는 역할이 존재하지 않거나 비활성 상태입니다."
}
INVALID_PROJECT_STATE = {"description": "프로젝트 상태 또는 일정 변경 규칙을 위반했습니다."}


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="프로젝트 모집 글 생성",
    description=(
        "로그인한 사용자가 프로젝트 기본 정보와 토픽, 기술 스택, 모집 포지션, "
        "협업 채널을 하나의 요청으로 등록합니다."
    ),
    operation_id="PROJECT_001_create",
    responses={
        400: VALIDATION_ERROR,
        401: AUTHENTICATION_REQUIRED,
        409: INVALID_PROJECT_STATE,
        422: INVALID_PROJECT_SELECTION,
    },
)
def create_project(
    request: ProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """프로젝트 모집 글과 하위 모집 정보를 생성한다."""
    return {"data": ProjectService.create(db, user, request)}


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="프로젝트 모집 글 목록 조회",
    description=(
        "공개 프로젝트를 최신순으로 조회합니다. 작성자, 모집 상태, 진행 방식, 토픽, "
        "기술 스택, 역할 및 검색어 필터를 함께 사용할 수 있습니다."
    ),
    operation_id="PROJECT_002_list",
    responses={400: VALIDATION_ERROR, 401: AUTHENTICATION_REQUIRED},
)
def list_projects(
    page: int = Query(1, ge=1, description="조회할 페이지 번호", examples=[1]),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수", examples=[20]),
    owner_user_id: int | None = Query(
        None, alias="ownerUserId", gt=0, description="작성자 사용자 식별자"
    ),
    recruitment_status: Literal["DRAFT", "RECRUITING", "CLOSED"] | None = Query(
        None, alias="recruitmentStatus", description="모집 상태"
    ),
    work_type: Literal["ONLINE", "OFFLINE", "HYBRID"] | None = Query(
        None, alias="workType", description="진행 방식"
    ),
    topic_id: int | None = Query(None, alias="topicId", gt=0, description="토픽 식별자"),
    tech_stack_id: int | None = Query(
        None, alias="techStackId", gt=0, description="기술 스택 식별자"
    ),
    role_id: int | None = Query(None, alias="roleId", gt=0, description="모집 역할 식별자"),
    keyword: str | None = Query(None, max_length=100, description="제목과 요약에서 검색할 문자열"),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """조건에 맞는 공개 프로젝트 목록을 페이지 단위로 반환한다."""
    return {
        "data": ProjectService.list(
            db,
            page=page,
            size=size,
            owner_user_id=owner_user_id,
            recruitment_status=recruitment_status,
            work_type=work_type,
            topic_id=topic_id,
            tech_stack_id=tech_stack_id,
            role_id=role_id,
            keyword=keyword,
        )
    }


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="프로젝트 모집 글 상세 조회",
    description=(
        "프로젝트 기본 정보와 토픽, 기술 스택, 모집 포지션 및 활성 협업 채널을 조회합니다. "
        "비공개 프로젝트는 작성자만 조회할 수 있습니다."
    ),
    operation_id="PROJECT_003_detail",
    responses={401: AUTHENTICATION_REQUIRED, 404: PROJECT_NOT_FOUND},
)
def get_project(
    project_id: int = Path(gt=0, description="조회할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """프로젝트 모집 글의 상세 정보를 반환한다."""
    return {"data": ProjectService.get(db, project_id, user)}


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="프로젝트 모집 글 수정",
    description=(
        "작성자가 프로젝트 정보와 모집 상태 또는 하위 모집 정보를 부분 수정합니다. "
        "목록형 하위 정보는 전달된 경우 전체 교체됩니다."
    ),
    operation_id="PROJECT_004_update",
    responses={
        400: VALIDATION_ERROR,
        401: AUTHENTICATION_REQUIRED,
        403: PROJECT_PERMISSION_DENIED,
        404: PROJECT_NOT_FOUND,
        409: INVALID_PROJECT_STATE,
        422: INVALID_PROJECT_SELECTION,
    },
)
def update_project(
    request: ProjectUpdateRequest,
    project_id: int = Path(gt=0, description="수정할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """작성자 권한과 상태 규칙을 검증한 뒤 프로젝트를 수정한다."""
    return {"data": ProjectService.update(db, user, project_id, request)}


@router.delete(
    "/{project_id}",
    response_model=ProjectDeleteResponse,
    summary="프로젝트 모집 글 삭제",
    description="작성자가 삭제 사유를 입력하여 프로젝트 모집 글을 소프트 삭제합니다.",
    operation_id="PROJECT_005_delete",
    responses={
        400: VALIDATION_ERROR,
        401: AUTHENTICATION_REQUIRED,
        403: PROJECT_PERMISSION_DENIED,
        404: PROJECT_NOT_FOUND,
    },
)
def delete_project(
    request: ProjectDeleteRequest,
    project_id: int = Path(gt=0, description="삭제할 프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """작성자 권한을 확인하고 프로젝트를 복구 가능한 상태로 삭제한다."""
    return {"data": ProjectService.delete(db, user, project_id, request.reason)}
