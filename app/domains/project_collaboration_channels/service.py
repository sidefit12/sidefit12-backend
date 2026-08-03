"""프로젝트 협업 채널 서비스."""

from sqlalchemy.orm import Session

from app.domains.project_collaboration_channels.repository import (
    ProjectCollaborationChannelRepository,
)


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
