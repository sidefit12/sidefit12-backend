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
