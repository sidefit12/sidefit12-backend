"""토픽, 기술 스택, 역할 기준정보 조회 엔드포인트."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_optional_current_user
from app.domains.reference_data.exceptions import ReferenceDataAdminRequiredError
from app.domains.reference_data.openapi import (
    ROLES_EXAMPLE,
    TECH_STACKS_EXAMPLE,
    TOPICS_EXAMPLE,
    error_example,
    response_example,
)
from app.domains.reference_data.schemas import (
    RoleListResponse,
    TechStackListResponse,
    TopicListResponse,
)
from app.domains.roles.service import RoleService
from app.domains.tech_stacks.service import TechStackService
from app.domains.topics.service import TopicService
from app.domains.users.models import User

router = APIRouter(tags=["기준정보"])


def _validate_inactive_permission(include_inactive: bool, user: User | None) -> None:
    """비활성 항목 조회 요청자의 관리자 권한을 확인한다."""
    if include_inactive and (user is None or user.system_role != "ADMIN"):
        raise ReferenceDataAdminRequiredError()


def _request_id() -> str | None:
    """현재 요청의 추적 식별자를 반환한다."""
    return request_id_context.get()


COMMON_ERRORS = {
    400: error_example(
        "잘못된 조회 조건", "INVALID_QUERY_PARAMETER", "조회 조건이 올바르지 않습니다."
    ),
    403: error_example(
        "관리자 권한 필요",
        "ADMIN_PERMISSION_REQUIRED",
        "비활성 기준정보 조회에는 관리자 권한이 필요합니다.",
    ),
}


@router.get(
    "/topics",
    response_model=TopicListResponse,
    summary="토픽 목록 조회",
    description="활성 토픽 기준정보를 조회합니다. 관리자는 비활성 항목을 포함할 수 있습니다.",
    operation_id="MASTER_001_list_topics",
    responses={200: response_example("토픽 목록 조회 성공", TOPICS_EXAMPLE), **COMMON_ERRORS},
)
def list_topics(
    include_inactive: bool = Query(
        False,
        alias="includeInactive",
        description="비활성 토픽 포함 여부이며 관리자만 true를 사용할 수 있습니다.",
        examples=[False],
    ),
    keyword: str | None = Query(
        None,
        max_length=50,
        description="토픽 코드 또는 이름 검색어",
        examples=["핀테크"],
    ),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """조건에 맞는 토픽 목록을 반환한다."""
    _validate_inactive_permission(include_inactive, user)
    items = TopicService.list(db, include_inactive=include_inactive, keyword=keyword)
    return {"success": True, "data": {"items": items}, "requestId": _request_id()}


@router.get(
    "/tech-stacks",
    response_model=TechStackListResponse,
    summary="기술 스택 목록 조회",
    description="활성 기술 스택 기준정보를 카테고리와 함께 조회합니다. 관리자는 비활성 항목을 포함할 수 있습니다.",
    operation_id="MASTER_002_list_tech_stacks",
    responses={
        200: response_example("기술 스택 목록 조회 성공", TECH_STACKS_EXAMPLE),
        **COMMON_ERRORS,
    },
)
def list_tech_stacks(
    include_inactive: bool = Query(
        False,
        alias="includeInactive",
        description="비활성 기술 스택 포함 여부이며 관리자만 true를 사용할 수 있습니다.",
        examples=[False],
    ),
    keyword: str | None = Query(
        None,
        max_length=50,
        description="기술 스택 코드 또는 이름 검색어",
        examples=["Java"],
    ),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """조건에 맞는 기술 스택 목록을 반환한다."""
    _validate_inactive_permission(include_inactive, user)
    items = TechStackService.list(db, include_inactive=include_inactive, keyword=keyword)
    return {"success": True, "data": {"items": items}, "requestId": _request_id()}


@router.get(
    "/roles",
    response_model=RoleListResponse,
    summary="역할 목록 조회",
    description="활성 역할 기준정보를 조회합니다. 관리자는 비활성 항목을 포함할 수 있습니다.",
    operation_id="MASTER_003_list_roles",
    responses={200: response_example("역할 목록 조회 성공", ROLES_EXAMPLE), **COMMON_ERRORS},
)
def list_roles(
    include_inactive: bool = Query(
        False,
        alias="includeInactive",
        description="비활성 역할 포함 여부이며 관리자만 true를 사용할 수 있습니다.",
        examples=[False],
    ),
    keyword: str | None = Query(
        None,
        max_length=50,
        description="역할 코드 또는 이름 검색어",
        examples=["백엔드"],
    ),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """조건에 맞는 역할 목록을 반환한다."""
    _validate_inactive_permission(include_inactive, user)
    items = RoleService.list(db, include_inactive=include_inactive, keyword=keyword)
    return {"success": True, "data": {"items": items}, "requestId": _request_id()}
