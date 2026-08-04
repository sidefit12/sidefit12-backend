"""프로젝트 리뷰 API 라우터."""

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user, get_optional_current_user
from app.domains.project_reviews.openapi import ONE, PAGE, error_example, response_example
from app.domains.project_reviews.schemas import (
    ReviewCreateRequest,
    ReviewPageResponse,
    ReviewResponse,
    ReviewUpdateRequest,
)
from app.domains.project_reviews.service import ProjectReviewService
from app.domains.users.models import User

router = APIRouter(tags=["프로젝트 리뷰"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")


@router.get(
    "/projects/{projectId}/reviews",
    response_model=ReviewPageResponse,
    summary="프로젝트 리뷰 목록 조회",
    description="프로젝트 리뷰와 평균 평점을 페이지로 조회합니다.",
    operation_id="REVIEW_001",
    responses={
        200: response_example("리뷰 목록 조회 성공", PAGE),
        404: error_example("프로젝트 없음", "PROJECT_NOT_FOUND", "프로젝트를 찾을 수 없습니다."),
    },
)
def list_reviews(
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    sort: Literal["LATEST", "RATING_HIGH", "RATING_LOW"] = Query(
        "LATEST", description="리뷰 정렬 기준"
    ),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    data, meta = ProjectReviewService.page(db, project_id, user, page=page, size=size, sort=sort)
    return {"success": True, "data": data, "meta": meta, "requestId": request_id_context.get()}


@router.post(
    "/projects/{projectId}/reviews",
    response_model=ReviewResponse,
    status_code=201,
    summary="프로젝트 리뷰 작성",
    description="완료 프로젝트 참여자가 리뷰를 한 번 작성합니다.",
    operation_id="REVIEW_002",
    responses={
        201: response_example("리뷰 작성 성공", ONE),
        401: AUTH,
        403: error_example("접근 거부", "ACCESS_DENIED", "접근 권한이 없습니다."),
        409: error_example("중복 리뷰", "REVIEW_ALREADY_EXISTS", "이미 리뷰를 작성했습니다."),
    },
)
def create_review(
    request: ReviewCreateRequest,
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ProjectReviewService.create(db, user, project_id, request),
        "requestId": request_id_context.get(),
    }


@router.patch(
    "/reviews/{reviewId}",
    response_model=ReviewResponse,
    summary="프로젝트 리뷰 수정",
    description="작성자가 자신의 리뷰를 부분 수정합니다.",
    operation_id="REVIEW_003",
    responses={
        200: response_example("리뷰 수정 성공", ONE),
        401: AUTH,
        403: error_example(
            "작성자 권한 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
        404: error_example("리뷰 없음", "REVIEW_NOT_FOUND", "리뷰를 찾을 수 없습니다."),
    },
)
def update_review(
    request: ReviewUpdateRequest,
    review_id: int = Path(alias="reviewId", ge=1, description="리뷰 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ProjectReviewService.update(db, user, review_id, request),
        "requestId": request_id_context.get(),
    }


@router.delete(
    "/reviews/{reviewId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="프로젝트 리뷰 삭제",
    description="작성자가 자신의 리뷰를 삭제합니다.",
    operation_id="REVIEW_004",
    responses={
        401: AUTH,
        403: error_example(
            "작성자 권한 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
        ),
        404: error_example("리뷰 없음", "REVIEW_NOT_FOUND", "리뷰를 찾을 수 없습니다."),
    },
)
def delete_review(
    review_id: int = Path(alias="reviewId", ge=1, description="리뷰 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectReviewService.delete(db, user, review_id)
    return Response(status_code=204)
