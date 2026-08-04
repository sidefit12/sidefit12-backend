"""프로젝트 협업 채널 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_collaboration_channels.exceptions import (
    ChannelAccessDeniedError,
    ChannelNotFoundError,
)
from app.domains.project_collaboration_channels.repository import (
    ProjectCollaborationChannelRepository,
)
from app.domains.project_collaboration_channels.schemas import ChannelResource
from app.domains.project_members.service import ProjectMemberService
from app.domains.users.models import User


class ProjectCollaborationChannelService:
    """Projects 도메인에 협업 채널 연산을 제공한다."""

    @staticmethod
    def replace(db: Session, project_id: int, user_id: int, items) -> None:
        """프로젝트 협업 채널을 전체 교체한다."""
        ProjectCollaborationChannelRepository.replace(db, project_id, user_id, items)

    @staticmethod
    def list_active_by_project(db: Session, project_id: int):
        """프로젝트의 활성 협업 채널을 조회한다."""
        return ProjectCollaborationChannelRepository.list_active_by_project(db, project_id)

    @staticmethod
    def list_for_member(db: Session, user: User, project_id: int):
        """활성 프로젝트 팀원에게 협업 채널을 반환한다."""
        from app.domains.projects.service import ProjectService

        ProjectService.get_for_application(db, project_id)
        if not ProjectMemberService.is_active_member(db, project_id, user.user_id):
            raise ChannelAccessDeniedError()
        return [
            ChannelResource.model_validate(item)
            for item in ProjectCollaborationChannelRepository.list_active_by_project(db, project_id)
        ]

    @staticmethod
    def create(db: Session, user: User, project_id: int, request):
        from app.domains.projects.service import ProjectService

        ProjectService.require_owner(db, user, project_id)
        channel = ProjectCollaborationChannelRepository.add(
            db, project_id=project_id, user_id=user.user_id, request=request
        )
        db.commit()
        db.refresh(channel)
        return ChannelResource.model_validate(channel)

    @staticmethod
    def update(db: Session, user: User, project_id: int, channel_id: int, request):
        from app.domains.projects.service import ProjectService

        ProjectService.require_owner(db, user, project_id)
        channel = ProjectCollaborationChannelRepository.find(db, project_id, channel_id)
        if channel is None:
            raise ChannelNotFoundError()
        for field in request.model_fields_set:
            value = getattr(request, field)
            if value is not None:
                setattr(channel, field, str(value) if field == "channel_url" else value)
        from datetime import datetime, timezone

        channel.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ChannelResource.model_validate(channel)

    @staticmethod
    def delete(db: Session, user: User, project_id: int, channel_id: int):
        from app.domains.projects.service import ProjectService

        ProjectService.require_owner(db, user, project_id)
        channel = ProjectCollaborationChannelRepository.find(db, project_id, channel_id)
        if channel is None:
            raise ChannelNotFoundError()
        channel.is_active = False
        db.commit()
