"""프로젝트 팀원 조회와 상태 변경 비즈니스 로직."""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.notifications.service import NotificationService
from app.domains.project_member_events.service import ProjectMemberEventService
from app.domains.project_members.exceptions import (
    MemberAccessDeniedError,
    MemberInvalidStateTransitionError,
    MemberNotFoundError,
    MemberPositionCapacityExceededError,
)
from app.domains.project_members.repository import ProjectMemberRepository
from app.domains.project_members.schemas import (
    ChannelResource,
    MemberData,
    MemberEventPageData,
    MemberEventResource,
    MemberListData,
    MemberResource,
    MemberUserSummary,
    PageMeta,
    PositionCapacity,
)
from app.domains.project_positions.service import ProjectPositionService
from app.domains.user_profiles.repository import ProfileRepository
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User
from app.domains.users.service import UserService


class ProjectMemberService:
    """MEMBER-001~005와 프로젝트 생성·승인에 필요한 팀원 규칙을 제공한다."""

    @staticmethod
    def add_owner(db: Session, project_id: int, user_id: int) -> None:
        member = ProjectMemberRepository.add_owner(db, project_id, user_id)
        ProjectMemberEventService.add_joined(db, member.project_member_id, user_id)

    @staticmethod
    def add_accepted_member(
        db: Session,
        *,
        project_id: int,
        user_id: int,
        position_id: int,
        application_id: int,
        actor_user_id: int,
    ):
        """승인된 지원자를 추가하고 합류 이벤트를 기록한다."""
        member = ProjectMemberRepository.add_member(
            db,
            project_id=project_id,
            user_id=user_id,
            position_id=position_id,
            application_id=application_id,
        )
        ProjectMemberEventService.add_joined(db, member.project_member_id, actor_user_id)
        return member

    @staticmethod
    def active_count(db: Session, project_id: int) -> int:
        return ProjectMemberRepository.active_member_count(db, project_id)

    @staticmethod
    def has_confirmed_members(db: Session, project_id: int) -> bool:
        return ProjectMemberRepository.active_member_count(db, project_id, exclude_owner=True) > 0

    @staticmethod
    def is_active_member(db: Session, project_id: int, user_id: int) -> bool:
        """사용자가 프로젝트의 활성 팀원인지 확인한다."""
        member = ProjectMemberRepository.find_by_user(db, project_id, user_id)
        return member is not None and member.member_status == "ACTIVE"

    @staticmethod
    def is_active_or_former_member(db: Session, project_id: int, user_id: int) -> bool:
        """사용자가 프로젝트에 참여한 이력이 있는지 확인한다."""
        return ProjectMemberRepository.find_by_user(db, project_id, user_id) is not None

    @staticmethod
    def active_position_count(db: Session, project_id: int, position_id: int) -> int:
        """자동 모집 종료에서 포지션의 활성 일반 팀원 수를 제공한다."""
        return ProjectMemberRepository.active_position_count(db, project_id, position_id)

    @staticmethod
    def list_members(
        db: Session,
        user: User,
        project_id: int,
        *,
        status: str | None,
        include_channels: bool,
    ) -> MemberListData:
        """팀원 목록, 포지션 충원 현황과 권한에 따른 협업 채널을 반환한다."""
        from app.domains.projects.service import ProjectService

        project = ProjectService.get_for_application(db, project_id)
        requester = ProjectMemberRepository.find_by_user(db, project_id, user.user_id)
        is_active_member = requester is not None and requester.member_status == "ACTIVE"
        if include_channels and not is_active_member:
            raise MemberAccessDeniedError()
        members = ProjectMemberRepository.list_by_project(db, project_id, status=status)
        positions = ProjectPositionService.list_by_project(db, project_id)
        channels = None
        if include_channels:
            from app.domains.project_collaboration_channels.service import (
                ProjectCollaborationChannelService,
            )

            channels = [
                ChannelResource(
                    project_collaboration_channel_id=channel.project_collaboration_channel_id,
                    channel_type=channel.channel_type,
                    channel_name=channel.channel_name,
                    channel_url=channel.channel_url,
                )
                for channel in ProjectCollaborationChannelService.list_active_by_project(
                    db, project_id
                )
            ]
        return MemberListData(
            items=[
                ProjectMemberService._resource(
                    db,
                    member,
                    user,
                    expose_private=(
                        user.user_id == project.owner_user_id or user.user_id == member.user_id
                    ),
                )
                for member in members
            ],
            position_summary={
                str(position.project_position_id): PositionCapacity(
                    project_position_id=position.project_position_id,
                    position_title=position.position_title,
                    required_count=position.required_count,
                    active_count=ProjectMemberRepository.active_position_count(
                        db, project_id, position.project_position_id
                    ),
                    position_status=position.position_status,
                )
                for position in positions
            },
            channels=channels,
        )

    @staticmethod
    def leave(db: Session, user: User, project_id: int, reason: str | None) -> MemberData:
        """활성 일반 팀원을 탈퇴 상태로 변경한다."""
        member = ProjectMemberRepository.find_by_user(db, project_id, user.user_id, lock=True)
        if member is None:
            raise MemberNotFoundError()
        if member.member_type == "OWNER":
            raise MemberInvalidStateTransitionError()
        if member.member_status == "LEFT":
            return MemberData(member=ProjectMemberService._resource(db, member, user))
        if member.member_status != "ACTIVE":
            raise MemberInvalidStateTransitionError()
        member.member_status = "LEFT"
        member.left_at = datetime.now(timezone.utc)
        position = ProjectPositionService.find(db, member.project_position_id, lock=True)
        ProjectPositionService.open(db, position)
        ProjectMemberEventService.add_status_event(
            db,
            project_member_id=member.project_member_id,
            event_type="LEFT",
            actor_user_id=user.user_id,
            reason=reason.strip() if reason else None,
        )
        from app.domains.projects.service import ProjectService

        project = ProjectService.get_for_application(db, project_id)
        NotificationService.team_member_changed(
            db, project.owner_user_id, project_id, event_type="LEFT"
        )
        db.commit()
        return MemberData(member=ProjectMemberService._resource(db, member, user))

    @staticmethod
    def remove(db: Session, user: User, project_id: int, member_id: int, reason: str) -> MemberData:
        """프로젝트 소유자가 활성 일반 팀원을 퇴출한다."""
        from app.domains.projects.service import ProjectService

        ProjectService.require_owner(db, user, project_id)
        member = ProjectMemberRepository.find(db, member_id, lock=True)
        ProjectMemberService._validate_target(member, project_id)
        if member.member_type == "OWNER":
            raise MemberInvalidStateTransitionError()
        if member.member_status == "REMOVED":
            return MemberData(member=ProjectMemberService._resource(db, member, user))
        if member.member_status != "ACTIVE":
            raise MemberInvalidStateTransitionError()
        member.member_status = "REMOVED"
        member.left_at = datetime.now(timezone.utc)
        position = ProjectPositionService.find(db, member.project_position_id, lock=True)
        ProjectPositionService.open(db, position)
        ProjectMemberEventService.add_status_event(
            db,
            project_member_id=member.project_member_id,
            event_type="REMOVED",
            actor_user_id=user.user_id,
            reason=reason.strip(),
        )
        NotificationService.team_member_changed(
            db, member.user_id, project_id, event_type="REMOVED"
        )
        db.commit()
        return MemberData(member=ProjectMemberService._resource(db, member, user))

    @staticmethod
    def restore(
        db: Session, user: User, project_id: int, member_id: int, reason: str | None
    ) -> MemberData:
        """프로젝트 소유자가 탈퇴 또는 퇴출 팀원을 정원 내에서 복구한다."""
        from app.domains.projects.service import ProjectService

        ProjectService.require_owner(db, user, project_id)
        member = ProjectMemberRepository.find(db, member_id, lock=True)
        ProjectMemberService._validate_target(member, project_id)
        if member.member_type == "OWNER":
            raise MemberInvalidStateTransitionError()
        if member.member_status == "ACTIVE":
            return MemberData(member=ProjectMemberService._resource(db, member, user))
        if member.member_status not in {"LEFT", "REMOVED"}:
            raise MemberInvalidStateTransitionError()
        position = ProjectPositionService.find(db, member.project_position_id, lock=True)
        active_count = ProjectMemberRepository.active_position_count(
            db, project_id, member.project_position_id
        )
        if active_count >= position.required_count:
            raise MemberPositionCapacityExceededError()
        member.member_status = "ACTIVE"
        member.left_at = None
        if active_count + 1 >= position.required_count:
            ProjectPositionService.close(db, position)
        ProjectMemberEventService.add_status_event(
            db,
            project_member_id=member.project_member_id,
            event_type="RESTORED",
            actor_user_id=user.user_id,
            reason=reason.strip() if reason else None,
        )
        NotificationService.team_member_changed(
            db, member.user_id, project_id, event_type="RESTORED"
        )
        db.commit()
        return MemberData(member=ProjectMemberService._resource(db, member, user))

    @staticmethod
    def event_page(db: Session, user: User, project_id: int, *, page: int, size: int):
        """활성 팀원에게 프로젝트 팀원 변경 이력을 반환한다."""
        requester = ProjectMemberRepository.find_by_user(db, project_id, user.user_id)
        if requester is None or requester.member_status != "ACTIVE":
            raise MemberAccessDeniedError()
        members = ProjectMemberRepository.list_by_project(db, project_id)
        events, total = ProjectMemberEventService.page_by_member_ids(
            db, {member.project_member_id for member in members}, page=page, size=size
        )
        items = []
        for event in events:
            actor = UserService.get_by_id(db, event.actor_user_id) if event.actor_user_id else None
            items.append(
                MemberEventResource(
                    event_type=event.event_type,
                    reason=event.reason,
                    created_at=event.created_at,
                    actor=ProjectMemberService._user_summary(db, actor, user) if actor else None,
                )
            )
        return MemberEventPageData(items=items), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )

    @staticmethod
    def _resource(
        db: Session, member, viewer: User, *, expose_private: bool = False
    ) -> MemberResource:
        user = UserService.get_by_id(db, member.user_id)
        return MemberResource(
            project_member_id=member.project_member_id,
            project_id=member.project_id,
            project_position_id=member.project_position_id,
            member_type=member.member_type,
            member_status=member.member_status,
            joined_at=member.joined_at,
            left_at=member.left_at,
            user=ProjectMemberService._user_summary(
                db, user, viewer, expose_private=expose_private
            ),
        )

    @staticmethod
    def _user_summary(
        db: Session, user: User, viewer: User, *, expose_private: bool = False
    ) -> MemberUserSummary:
        profile = ProfileService.get_user_summary(db, user.user_id)
        stored_profile = ProfileRepository.find_profile(db, user.user_id)
        return MemberUserSummary(
            user_id=user.user_id,
            nickname=user.nickname,
            user_status=user.user_status,
            system_role=user.system_role,
            onboarding_completed=bool(profile["onboarding_completed"]),
            profile_image_url=profile["profile_image_url"],
            email=user.email if viewer.user_id == user.user_id else None,
            introduction=stored_profile.introduction if stored_profile else None,
            external_link_url=stored_profile.external_link_url if stored_profile else None,
            career_level=stored_profile.career_level if stored_profile and expose_private else None,
            preferred_work_type=(
                stored_profile.preferred_work_type if stored_profile and expose_private else None
            ),
            preferred_region=(
                stored_profile.preferred_region if stored_profile and expose_private else None
            ),
            available_start_date=(
                stored_profile.available_start_date if stored_profile and expose_private else None
            ),
            available_end_date=(
                stored_profile.available_end_date if stored_profile and expose_private else None
            ),
            available_hours_per_week=(
                stored_profile.available_hours_per_week
                if stored_profile and expose_private
                else None
            ),
            topics=ProfileService._selected_topics(db, user.user_id),
            tech_stacks=ProfileService._selected_tech_stacks(db, user.user_id),
            roles=ProfileService._selected_roles(db, user.user_id),
        )

    @staticmethod
    def _validate_target(member, project_id: int) -> None:
        if member is None or member.project_id != project_id:
            raise MemberNotFoundError(member.project_member_id if member else None)
