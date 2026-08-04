"""홈 화면 API 라우터."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.home.schemas import HomeResponse
from app.domains.home.service import HomeService
from app.domains.users.models import User

router = APIRouter(tags=["홈"])


@router.get(
    "/home",
    response_model=HomeResponse,
    summary="홈 화면 정보 조회",
    description="프로필·활동 요약과 개인화 추천·최신·마감 임박 프로젝트를 조합해 반환합니다.",
    operation_id="HOME_001",
    responses={401: {"description": "로그인이 필요합니다."}},
)
def home(
    section_size: int = Query(6, alias="sectionSize", ge=1, le=20, description="영역별 반환 개수"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"data": HomeService.get(db, user, section_size), "requestId": request_id_context.get()}
