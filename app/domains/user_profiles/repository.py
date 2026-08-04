"""사용자 프로필과 선택 관계 데이터 접근 repository."""

from collections.abc import Sequence

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.domains.roles.models import Role
from app.domains.tech_stacks.models import TechStack
from app.domains.topics.models import Topic
from app.domains.user_profiles.models import (
    UserProfile,
    UserRole,
    UserTechStack,
    UserTopic,
)


class ProfileRepository:
    """프로필 기본 정보와 토픽·기술·역할 관계의 영속성을 관리한다."""

    @staticmethod
    def find_profile(db: Session, user_id: int) -> UserProfile | None:
        """사용자 식별자로 프로필을 조회한다."""
        return db.get(UserProfile, user_id)

    @staticmethod
    def get_or_create_profile(db: Session, user_id: int) -> UserProfile:
        """프로필이 없으면 기본 프로필을 생성해 반환한다."""
        profile = ProfileRepository.find_profile(db, user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            db.flush()
        return profile

    @staticmethod
    def detach_file_references(db: Session, file_id: int) -> None:
        """지정한 파일을 참조하는 프로필 컬럼을 NULL로 변경한다."""
        profiles = db.scalars(
            select(UserProfile).where(
                or_(
                    UserProfile.profile_image_file_id == file_id,
                    UserProfile.public_material_file_id == file_id,
                )
            )
        ).all()
        for profile in profiles:
            if profile.profile_image_file_id == file_id:
                profile.profile_image_file_id = None
            if profile.public_material_file_id == file_id:
                profile.public_material_file_id = None

    @staticmethod
    def anonymize(db: Session, user_id: int) -> None:
        """탈퇴 사용자의 프로필 개인정보와 선택 관계를 제거한다."""
        profile = ProfileRepository.find_profile(db, user_id)
        if profile is not None:
            profile.introduction = None
            profile.external_link_url = None
            profile.profile_image_file_id = None
            profile.public_material_file_id = None
            profile.career_level = None
            profile.preferred_work_type = None
            profile.preferred_region = None
            profile.available_start_date = None
            profile.available_end_date = None
            profile.available_hours_per_week = None
            profile.onboarding_completed = False
        db.execute(delete(UserTopic).where(UserTopic.user_id == user_id))
        db.execute(delete(UserTechStack).where(UserTechStack.user_id == user_id))
        db.execute(delete(UserRole).where(UserRole.user_id == user_id))

    @staticmethod
    def list_topics(db: Session, user_id: int) -> Sequence[tuple[UserTopic, Topic]]:
        """사용자의 관심 토픽 관계와 기준정보를 함께 조회한다."""
        return db.execute(
            select(UserTopic, Topic)
            .join(Topic, Topic.topic_id == UserTopic.topic_id)
            .where(UserTopic.user_id == user_id)
            .order_by(UserTopic.priority, Topic.topic_name)
        ).all()

    @staticmethod
    def replace_topics(db: Session, user_id: int, topic_ids: list[int]) -> None:
        """사용자의 관심 토픽을 전달받은 순서로 교체한다."""
        db.execute(delete(UserTopic).where(UserTopic.user_id == user_id))
        db.add_all(
            [
                UserTopic(user_id=user_id, topic_id=topic_id, priority=index)
                for index, topic_id in enumerate(topic_ids)
            ]
        )

    @staticmethod
    def list_tech_stacks(db: Session, user_id: int) -> Sequence[tuple[UserTechStack, TechStack]]:
        """사용자의 기술 스택 관계와 기준정보를 함께 조회한다."""
        return db.execute(
            select(UserTechStack, TechStack)
            .join(TechStack, TechStack.tech_stack_id == UserTechStack.tech_stack_id)
            .where(UserTechStack.user_id == user_id)
            .order_by(TechStack.category, TechStack.tech_stack_name)
        ).all()

    @staticmethod
    def replace_tech_stacks(db: Session, user_id: int, items) -> None:
        """사용자의 기술 스택 관계를 요청 목록으로 교체한다."""
        db.execute(delete(UserTechStack).where(UserTechStack.user_id == user_id))
        db.add_all(
            [
                UserTechStack(
                    user_id=user_id,
                    tech_stack_id=item.tech_stack_id,
                    proficiency_level=item.proficiency_level,
                    experience_months=item.experience_months,
                    is_learning=item.is_learning,
                )
                for item in items
            ]
        )

    @staticmethod
    def list_roles(db: Session, user_id: int) -> Sequence[tuple[UserRole, Role]]:
        """사용자의 희망 역할 관계와 기준정보를 함께 조회한다."""
        return db.execute(
            select(UserRole, Role)
            .join(Role, Role.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
            .order_by(UserRole.priority, Role.role_name)
        ).all()

    @staticmethod
    def replace_roles(db: Session, user_id: int, items) -> None:
        """사용자의 희망 역할 관계를 요청 목록으로 교체한다."""
        db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        db.add_all(
            [
                UserRole(
                    user_id=user_id,
                    role_id=item.role_id,
                    priority=item.priority,
                    experience_level=item.experience_level,
                )
                for item in items
            ]
        )
