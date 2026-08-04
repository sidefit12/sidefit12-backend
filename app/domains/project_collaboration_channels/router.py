"""프로젝트 협업 채널 API 라우터."""

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import request_id_context
from app.domains.auth.dependencies import get_current_user
from app.domains.project_collaboration_channels.openapi import (
    LIST,
    ONE,
    error_example,
    response_example,
)
from app.domains.project_collaboration_channels.schemas import (
    ChannelCreateRequest,
    ChannelListResponse,
    ChannelResponse,
    ChannelUpdateRequest,
)
from app.domains.project_collaboration_channels.service import ProjectCollaborationChannelService
from app.domains.users.models import User

router = APIRouter(tags=["프로젝트 협업 채널"])
AUTH = error_example("인증 필요", "AUTHENTICATION_REQUIRED", "로그인이 필요합니다.")
OWNER = error_example(
    "소유자 권한 필요", "RESOURCE_OWNERSHIP_REQUIRED", "리소스 소유자만 처리할 수 있습니다."
)


@router.get(
    "/projects/{projectId}/channels",
    response_model=ChannelListResponse,
    summary="프로젝트 협업 채널 조회",
    description="프로젝트의 활성 팀원에게 활성 협업 채널을 반환합니다.",
    operation_id="CHANNEL_001",
    responses={
        200: response_example("협업 채널 조회 성공", LIST),
        401: AUTH,
        403: error_example("접근 거부", "ACCESS_DENIED", "접근 권한이 없습니다."),
        404: error_example("프로젝트 없음", "PROJECT_NOT_FOUND", "프로젝트를 찾을 수 없습니다."),
    },
)
def list_channels(
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": {"items": ProjectCollaborationChannelService.list_for_member(db, user, project_id)},
        "requestId": request_id_context.get(),
    }


@router.post(
    "/projects/{projectId}/channels",
    response_model=ChannelResponse,
    status_code=201,
    summary="프로젝트 협업 채널 등록",
    description="프로젝트 소유자가 협업 채널을 등록합니다.",
    operation_id="CHANNEL_002",
    responses={201: response_example("협업 채널 등록 성공", ONE), 401: AUTH, 403: OWNER},
)
def create_channel(
    request: ChannelCreateRequest,
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ProjectCollaborationChannelService.create(db, user, project_id, request),
        "requestId": request_id_context.get(),
    }


@router.patch(
    "/projects/{projectId}/channels/{channelId}",
    response_model=ChannelResponse,
    summary="프로젝트 협업 채널 수정",
    description="프로젝트 소유자가 채널 정보를 부분 수정합니다.",
    operation_id="CHANNEL_003",
    responses={
        200: response_example("협업 채널 수정 성공", ONE),
        401: AUTH,
        403: OWNER,
        404: error_example("채널 없음", "CHANNEL_NOT_FOUND", "협업 채널을 찾을 수 없습니다."),
    },
)
def update_channel(
    request: ChannelUpdateRequest,
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    channel_id: int = Path(alias="channelId", ge=1, description="협업 채널 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "success": True,
        "data": ProjectCollaborationChannelService.update(
            db, user, project_id, channel_id, request
        ),
        "requestId": request_id_context.get(),
    }


@router.delete(
    "/projects/{projectId}/channels/{channelId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="프로젝트 협업 채널 삭제",
    description="프로젝트 소유자가 협업 채널을 멱등하게 비활성화합니다.",
    operation_id="CHANNEL_004",
    responses={
        401: AUTH,
        403: OWNER,
        404: error_example("채널 없음", "CHANNEL_NOT_FOUND", "협업 채널을 찾을 수 없습니다."),
    },
)
def delete_channel(
    project_id: int = Path(alias="projectId", ge=1, description="프로젝트 식별자"),
    channel_id: int = Path(alias="channelId", ge=1, description="협업 채널 식별자"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectCollaborationChannelService.delete(db, user, project_id, channel_id)
    return Response(status_code=204)
