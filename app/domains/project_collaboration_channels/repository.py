"""프로젝트 협업 채널 데이터 접근 연산."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.project_collaboration_channels.models import ProjectCollaborationChannel


class ProjectCollaborationChannelRepository:
    """협업 채널의 저장과 조회를 담당한다."""

    @staticmethod
    def replace(db: Session, project_id: int, user_id: int, items) -> None:
        """프로젝트의 협업 채널을 요청 목록으로 교체한다."""
        db.execute(
            delete(ProjectCollaborationChannel).where(
                ProjectCollaborationChannel.project_id == project_id
            )
        )
        db.add_all(
            [
                ProjectCollaborationChannel(
                    project_id=project_id,
                    channel_type=item.channel_type,
                    channel_name=item.channel_name.strip(),
                    channel_url=str(item.channel_url),
                    registered_by_user_id=user_id,
                )
                for item in items
            ]
        )

    @staticmethod
    def list_active_by_project(db: Session, project_id: int):
        """프로젝트의 활성 협업 채널을 조회한다."""
        return db.scalars(
            select(ProjectCollaborationChannel)
            .where(
                ProjectCollaborationChannel.project_id == project_id,
                ProjectCollaborationChannel.is_active.is_(True),
            )
            .order_by(ProjectCollaborationChannel.project_collaboration_channel_id)
        ).all()

    @staticmethod
    def find(db: Session, project_id: int, channel_id: int):
        """프로젝트에 속한 협업 채널을 조회한다."""
        return db.scalar(
            select(ProjectCollaborationChannel).where(
                ProjectCollaborationChannel.project_id == project_id,
                ProjectCollaborationChannel.project_collaboration_channel_id == channel_id,
            )
        )

    @staticmethod
    def add(db: Session, *, project_id: int, user_id: int, request):
        """새 협업 채널을 생성한다."""
        channel = ProjectCollaborationChannel(
            project_id=project_id,
            channel_type=request.channel_type,
            channel_name=request.channel_name.strip(),
            channel_url=str(request.channel_url),
            registered_by_user_id=user_id,
        )
        db.add(channel)
        db.flush()
        return channel
