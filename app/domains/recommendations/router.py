"""프로젝트 추천 API 라우터."""

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user, get_optional_current_user
from app.domains.recommendations.schemas import (
    AsyncJobResponse,
    ProjectListResponse,
    RecommendationPageResponse,
    RecommendationRefreshRequest,
)
from app.domains.recommendations.service import RecommendationService
from app.domains.users.models import User

router = APIRouter(tags=["추천"])


@router.get(
    "/recommendations/projects",
    response_model=RecommendationPageResponse,
    summary="개인화 프로젝트 추천 조회",
    description="사용자의 역할·토픽·기술 스택 일치 점수와 최대 3개의 추천 이유를 반환합니다.",
    operation_id="RECO_001",
    responses={
        401: {"description": "로그인이 필요합니다."},
        503: {"description": "추천 서비스를 사용할 수 없습니다."},
    },
)
def recommendations(
    cursor: str | None = Query(None, description="서버가 발급한 다음 페이지 커서"),
    size: int = Query(20, ge=1, le=50, description="한 번에 반환할 추천 개수"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data, meta = RecommendationService.page(db, user, cursor=cursor, size=size)
    return {"data": data, "meta": meta, "requestId": request_id_context.get()}


@router.get(
    "/projects/{projectId}/similar",
    response_model=ProjectListResponse,
    summary="유사 프로젝트 조회",
    description="현재 프로젝트와 토픽·기술·모집 역할이 유사한 모집 중 프로젝트를 반환합니다.",
    operation_id="RECO_002",
    responses={
        404: {"description": "프로젝트를 찾을 수 없습니다."},
        503: {"description": "추천 서비스를 사용할 수 없습니다."},
    },
)
def similar_projects(
    project_id: int = Path(alias="projectId", ge=1, description="기준 프로젝트 식별자"),
    size: int = Query(6, ge=1, le=6, description="반환할 유사 프로젝트 개수"),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    data = RecommendationService.similar(db, project_id, user, size)
    return {"data": data, "requestId": request_id_context.get()}


@router.post(
    "/recommendations/projects/refresh",
    response_model=AsyncJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="추천 결과 새로고침",
    description="저장된 추천 결과를 무효화하고 다음 조회에서 다시 계산하도록 요청합니다.",
    operation_id="RECO_003",
    responses={
        401: {"description": "로그인이 필요합니다."},
        429: {"description": "요청 횟수를 초과했습니다."},
        503: {"description": "추천 서비스를 사용할 수 없습니다."},
    },
)
def refresh_recommendations(
    request: RecommendationRefreshRequest | None = Body(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = RecommendationService.refresh(db, user, request.force if request else False)
    return {"data": data, "requestId": request_id_context.get()}
