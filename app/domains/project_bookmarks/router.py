"""프로젝트 북마크 API 엔드포인트."""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.project_bookmarks.openapi import (
    BOOKMARKED_EXAMPLE,
    UNBOOKMARKED_EXAMPLE,
    error_example,
    response_example,
)
from app.domains.project_bookmarks.schemas import BookmarkStateResponse
from app.domains.project_bookmarks.service import ProjectBookmarkService
from app.domains.projects.openapi import PAGE_EXAMPLE
from app.domains.projects.schemas import ProjectPageResponse
from app.domains.users.models import User

router = APIRouter(tags=["프로젝트 북마크"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")
NOT_FOUND = error_example("프로젝트 없음", "PROJECT_NOT_FOUND", "프로젝트를 찾을 수 없습니다.")


def _request_id():
    return request_id_context.get()


@router.put(
    "/projects/{projectId}/bookmark",
    response_model=BookmarkStateResponse,
    summary="프로젝트 북마크 등록",
    description="사용자와 프로젝트의 북마크 관계를 멱등하게 생성합니다.",
    operation_id="BOOKMARK_001",
    responses={
        200: response_example("프로젝트 북마크 등록 성공", BOOKMARKED_EXAMPLE),
        401: AUTH,
        404: NOT_FOUND,
    },
)
def add_bookmark(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectBookmarkService.add(db, user, project_id)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.delete(
    "/projects/{projectId}/bookmark",
    response_model=BookmarkStateResponse,
    summary="프로젝트 북마크 해제",
    description="사용자와 프로젝트의 북마크 관계를 멱등하게 삭제합니다.",
    operation_id="BOOKMARK_002",
    responses={
        200: response_example("프로젝트 북마크 해제 성공", UNBOOKMARKED_EXAMPLE),
        401: AUTH,
        404: NOT_FOUND,
    },
)
def remove_bookmark(
    project_id: int = Path(alias="projectId", gt=0, description="프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = ProjectBookmarkService.remove(db, user, project_id)
    return {"success": True, "data": data, "requestId": _request_id()}


@router.get(
    "/users/me/bookmarks",
    response_model=ProjectPageResponse,
    summary="내 북마크 프로젝트 조회",
    description="저장한 프로젝트를 최신 북마크순으로 조회하며 삭제된 프로젝트는 제외합니다.",
    operation_id="BOOKMARK_003",
    responses={
        200: response_example("내 북마크 프로젝트 조회 성공", PAGE_EXAMPLE),
        401: AUTH,
    },
)
def list_my_bookmarks(
    include_closed: bool = Query(
        True, alias="includeClosed", description="모집 마감 프로젝트 포함 여부"
    ),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectBookmarkService.page(
        db,
        user,
        page=page,
        size=size,
        include_closed=include_closed,
    )
    return {
        "success": True,
        "data": data,
        "meta": meta,
        "requestId": _request_id(),
    }
