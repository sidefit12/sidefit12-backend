"""온보딩과 사용자 프로필 HTTP endpoint 모듈."""

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.schemas import WithdrawRequest
from app.domains.auth.service import AuthService
from app.domains.user_profiles.schemas import (
    ActivitySummaryResponse,
    OnboardingOptionsResponse,
    OnboardingRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    PublicProfileResponse,
    RoleSelectionResponse,
    RoleUpdateRequest,
    TechStackSelectionResponse,
    TechStackUpdateRequest,
    TopicSelectionResponse,
    TopicUpdateRequest,
)
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User
from app.integrations.object_storage import ObjectStorage, get_object_storage

router = APIRouter(tags=["프로필"])


@router.delete(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴",
    description="현재 비밀번호를 확인하고 개인정보를 익명화한 뒤 모든 세션을 폐기합니다.",
    operation_id="AUTH_012_withdraw",
    responses={
        400: {"description": "활성 프로젝트가 있어 탈퇴할 수 없습니다."},
        401: {"description": "현재 비밀번호가 일치하지 않습니다."},
    },
)
def withdraw(
    request: WithdrawRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """회원 탈퇴 요청을 처리한다."""
    AuthService.withdraw(db, user, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


AUTHENTICATION_REQUIRED = {
    "description": "로그인이 필요합니다.",
    "content": {
        "application/json": {
            "example": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "로그인이 필요합니다.",
                "details": None,
            }
        }
    },
}


@router.get(
    "/users/me/activity-summary",
    response_model=ActivitySummaryResponse,
    summary="내 활동 요약 조회",
    description="로그인 사용자의 작성 프로젝트, 상태별 지원, 북마크 건수를 반환합니다.",
    operation_id="PROFILE_009_activity_summary",
    responses={401: AUTHENTICATION_REQUIRED},
)
def activity_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """로그인 사용자의 프로젝트 활동 건수를 조회한다."""
    return {
        "success": True,
        "data": ProfileService.activity_summary(db, user),
        "requestId": request_id_context.get(),
    }


INVALID_SELECTION = {
    "description": "선택한 기준정보가 존재하지 않거나 비활성 상태입니다.",
    "content": {
        "application/json": {
            "example": {
                "code": "INVALID_PROFILE_SELECTION",
                "message": "선택한 프로필 항목을 사용할 수 없습니다.",
                "details": {"itemType": "topic", "invalidIds": [999]},
            }
        }
    },
}


@router.get(
    "/onboarding/options",
    response_model=OnboardingOptionsResponse,
    summary="온보딩 선택 정보 조회",
    description="활성 토픽·기술 스택·역할 목록과 현재 사용자의 선택값을 반환한다.",
    operation_id="PROFILE_001_onboarding_options",
    responses={401: AUTHENTICATION_REQUIRED},
)
def onboarding_options(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """로그인 사용자의 온보딩 선택지와 현재 선택값을 조회한다."""
    return {"data": ProfileService.onboarding_options(db, user)}


@router.put(
    "/users/me/onboarding",
    response_model=ProfileResponse,
    summary="온보딩 정보 일괄 저장",
    description="프로필 기본 정보와 토픽·기술 스택·희망 역할을 하나의 트랜잭션으로 저장한다.",
    operation_id="PROFILE_002_save_onboarding",
    responses={401: AUTHENTICATION_REQUIRED, 422: INVALID_SELECTION},
)
def save_onboarding(
    request: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
):
    """온보딩 입력값을 검증하고 로그인 사용자의 프로필에 저장한다."""
    return {"data": ProfileService.save_onboarding(db, user, request, storage)}


@router.get(
    "/users/me/profile",
    response_model=ProfileResponse,
    summary="내 프로필 조회",
    description="이메일과 참여 선호를 포함한 로그인 사용자의 전체 프로필을 반환한다.",
    operation_id="PROFILE_003_my_profile",
    responses={401: AUTHENTICATION_REQUIRED},
)
def my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
):
    """로그인 사용자의 상세 프로필을 조회한다."""
    return {"data": ProfileService.get_my_profile(db, user, storage)}


@router.get(
    "/users/{user_id}/profile",
    response_model=PublicProfileResponse,
    summary="공개 프로필 조회",
    description="이메일과 비공개 참여 선호를 제외한 활성 사용자의 공개 프로필을 반환한다.",
    operation_id="PROFILE_004_public_profile",
    responses={401: AUTHENTICATION_REQUIRED, 404: {"description": "프로필을 찾을 수 없습니다."}},
)
def public_profile(
    user_id: int = Path(..., gt=0, description="조회할 사용자 식별자"),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """지정한 활성 사용자의 공개 프로필을 조회한다."""
    return {"data": ProfileService.get_public_profile(db, user_id)}


@router.patch(
    "/users/me/profile",
    response_model=ProfileResponse,
    summary="기본 프로필 수정",
    description="닉네임, 자기소개, 참여 선호, 파일 참조와 공개 링크를 부분 수정한다.",
    operation_id="PROFILE_005_update_profile",
    responses={
        401: AUTHENTICATION_REQUIRED,
        409: {"description": "이미 사용 중인 닉네임입니다."},
    },
)
def update_profile(
    request: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
):
    """로그인 사용자의 기본 프로필을 부분 수정한다."""
    return {"data": ProfileService.update_profile(db, user, request, storage)}


@router.put(
    "/users/me/topics",
    response_model=TopicSelectionResponse,
    summary="관심 토픽 설정",
    description="활성 토픽을 최소 1개, 최대 10개까지 선택해 전체 교체한다.",
    operation_id="PROFILE_006_replace_topics",
    responses={401: AUTHENTICATION_REQUIRED, 422: INVALID_SELECTION},
)
def replace_topics(
    request: TopicUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """로그인 사용자의 관심 토픽 목록을 교체한다."""
    return {"data": ProfileService.replace_topics(db, user, request.topic_ids)}


@router.put(
    "/users/me/tech-stacks",
    response_model=TechStackSelectionResponse,
    summary="보유 기술 스택 설정",
    description="활성 기술 스택과 숙련 정보를 최대 20개까지 저장한다.",
    operation_id="PROFILE_007_replace_tech_stacks",
    responses={401: AUTHENTICATION_REQUIRED, 422: INVALID_SELECTION},
)
def replace_tech_stacks(
    request: TechStackUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """로그인 사용자의 기술 스택 목록을 교체한다."""
    return {"data": ProfileService.replace_tech_stacks(db, user, request.tech_stacks)}


@router.put(
    "/users/me/roles",
    response_model=RoleSelectionResponse,
    summary="희망 역할 설정",
    description="활성 역할을 최소 1개, 최대 3개까지 우선순위와 함께 저장한다.",
    operation_id="PROFILE_008_replace_roles",
    responses={401: AUTHENTICATION_REQUIRED, 422: INVALID_SELECTION},
)
def replace_roles(
    request: RoleUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """로그인 사용자의 희망 역할 목록을 교체한다."""
    return {"data": ProfileService.replace_roles(db, user, request.roles)}
