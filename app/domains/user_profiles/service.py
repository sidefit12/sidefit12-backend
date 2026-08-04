"""온보딩과 사용자 프로필 조회·수정 비즈니스 로직."""

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.roles.service import RoleService
from app.domains.tech_stacks.service import TechStackService
from app.domains.topics.service import TopicService
from app.domains.user_profiles.repository import ProfileRepository
from app.domains.user_profiles.schemas import (
    CurrentSelection,
    OnboardingOptionsData,
    OnboardingRequest,
    ProfileData,
    ProfileUpdateRequest,
    ProfileUser,
    PublicProfileData,
    RoleSelectionData,
    SelectedRole,
    SelectedTechStack,
    SelectedTopic,
    TechStackSelectionData,
    TopicSelectionData,
)
from app.domains.users.exceptions import (
    InvalidProfileDateRangeError,
    NicknameAlreadyExistsError,
    ProfileNotFoundError,
    UserNotFoundError,
)
from app.domains.users.models import User
from app.domains.users.service import UserService


class ProfileService:
    """PROFILE-001~008의 조회와 저장 규칙을 제공한다."""

    @staticmethod
    def get_user_summary(db: Session, user_id: int) -> dict[str, object]:
        """프로필 생성 없이 사용자 요약에 필요한 공개 상태를 반환한다."""
        profile = ProfileRepository.find_profile(db, user_id)
        return {
            "onboarding_completed": profile.onboarding_completed if profile else False,
            "profile_image_url": None,
        }

    @staticmethod
    def detach_file_references(db: Session, file_id: int) -> None:
        """파일 도메인의 삭제 요청에 따라 프로필 파일 참조를 해제한다."""
        ProfileRepository.detach_file_references(db, file_id)

    @staticmethod
    def onboarding_options(db: Session, user: User) -> OnboardingOptionsData:
        """활성 기준정보와 사용자의 현재 선택값을 반환한다."""
        topics = TopicService.list_active(db)
        tech_stacks = TechStackService.list_active(db)
        roles = RoleService.list_active(db)
        return OnboardingOptionsData(
            current_selection=CurrentSelection(
                topic_ids=[
                    relation.topic_id
                    for relation, _ in ProfileRepository.list_topics(db, user.user_id)
                ],
                tech_stack_ids=[
                    relation.tech_stack_id
                    for relation, _ in ProfileRepository.list_tech_stacks(db, user.user_id)
                ],
                role_ids=[
                    relation.role_id
                    for relation, _ in ProfileRepository.list_roles(db, user.user_id)
                ],
            ),
            topics=topics,
            tech_stacks=tech_stacks,
            roles=roles,
        )

    @staticmethod
    def save_onboarding(db: Session, user: User, request: OnboardingRequest) -> ProfileData:
        """프로필 기본값과 토픽·기술·역할 선택을 하나의 트랜잭션으로 저장한다."""
        TopicService.validate_active_ids(db, set(request.topic_ids))
        TechStackService.validate_active_ids(
            db, {item.tech_stack_id for item in request.tech_stacks}
        )
        RoleService.validate_active_ids(db, {item.role_id for item in request.roles})

        profile = ProfileRepository.get_or_create_profile(db, user.user_id)
        ProfileService._apply_profile_fields(profile, request, complete_onboarding=True)
        ProfileRepository.replace_topics(db, user.user_id, request.topic_ids)
        ProfileRepository.replace_tech_stacks(db, user.user_id, request.tech_stacks)
        ProfileRepository.replace_roles(db, user.user_id, request.roles)
        db.commit()
        return ProfileService.get_my_profile(db, user)

    @staticmethod
    def get_my_profile(db: Session, user: User) -> ProfileData:
        """이메일과 참여 선호 정보를 포함한 본인 프로필을 반환한다."""
        profile = ProfileRepository.get_or_create_profile(db, user.user_id)
        return ProfileService._profile_data(db, user, profile)

    @staticmethod
    def get_public_profile(db: Session, user_id: int) -> PublicProfileData:
        """활성 사용자의 공개 가능한 프로필 정보만 반환한다."""
        user = UserService.get_by_id(db, user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if user.user_status != "ACTIVE":
            raise ProfileNotFoundError(user_id)
        profile = ProfileRepository.find_profile(db, user_id)
        if profile is None:
            raise ProfileNotFoundError(user_id)
        data = ProfileService._profile_data(db, user, profile)
        return PublicProfileData(
            user_id=user.user_id,
            nickname=user.nickname,
            introduction=data.introduction,
            profile_image_file_id=data.profile_image_file_id,
            public_material_file_id=data.public_material_file_id,
            external_link_url=data.external_link_url,
            topics=data.topics,
            tech_stacks=data.tech_stacks,
            roles=data.roles,
        )

    @staticmethod
    def update_profile(db: Session, user: User, request: ProfileUpdateRequest) -> ProfileData:
        """닉네임, 기본 프로필, 파일 참조 및 공개 링크를 부분 수정한다."""
        if request.nickname is not None:
            nickname = request.nickname.strip()
            existing = UserService.get_by_nickname(db, nickname)
            if existing is not None and existing.user_id != user.user_id:
                raise NicknameAlreadyExistsError(nickname)
            UserService.update_nickname(db, user, nickname)

        profile = ProfileRepository.get_or_create_profile(db, user.user_id)
        ProfileService._validate_merged_dates(profile, request)
        ProfileService._apply_profile_fields(profile, request)

        if "profile_image_file_id" in request.model_fields_set:
            if request.profile_image_file_id is not None:
                from app.domains.files.service import FileService

                FileService.validate_profile_reference(
                    db, user.user_id, request.profile_image_file_id, "PROFILE_IMAGE"
                )
            profile.profile_image_file_id = request.profile_image_file_id
        if "public_material_file_id" in request.model_fields_set:
            if request.public_material_file_id is not None:
                from app.domains.files.service import FileService

                FileService.validate_profile_reference(
                    db, user.user_id, request.public_material_file_id, "PUBLIC_MATERIAL"
                )
            profile.public_material_file_id = request.public_material_file_id
        if "external_link_url" in request.model_fields_set:
            profile.external_link_url = (
                str(request.external_link_url) if request.external_link_url is not None else None
            )
        db.commit()
        return ProfileService.get_my_profile(db, user)

    @staticmethod
    def replace_topics(db: Session, user: User, topic_ids: list[int]) -> TopicSelectionData:
        """사용자의 관심 토픽을 검증 후 전체 교체한다."""
        TopicService.validate_active_ids(db, set(topic_ids))
        ProfileRepository.replace_topics(db, user.user_id, topic_ids)
        db.commit()
        return TopicSelectionData(topics=ProfileService._selected_topics(db, user.user_id))

    @staticmethod
    def replace_tech_stacks(db: Session, user: User, items) -> TechStackSelectionData:
        """사용자의 보유 기술 스택을 검증 후 전체 교체한다."""
        TechStackService.validate_active_ids(db, {item.tech_stack_id for item in items})
        ProfileRepository.replace_tech_stacks(db, user.user_id, items)
        db.commit()
        return TechStackSelectionData(
            tech_stacks=ProfileService._selected_tech_stacks(db, user.user_id)
        )

    @staticmethod
    def replace_roles(db: Session, user: User, items) -> RoleSelectionData:
        """사용자의 희망 역할을 검증 후 전체 교체한다."""
        RoleService.validate_active_ids(db, {item.role_id for item in items})
        ProfileRepository.replace_roles(db, user.user_id, items)
        db.commit()
        return RoleSelectionData(roles=ProfileService._selected_roles(db, user.user_id))

    @staticmethod
    def _profile_data(db: Session, user: User, profile) -> ProfileData:
        """ORM 데이터를 본인 프로필 응답 schema로 조합한다."""
        return ProfileData(
            user=ProfileUser(
                user_id=user.user_id,
                email=user.email,
                nickname=user.nickname,
                user_status=user.user_status,
                system_role=user.system_role,
                onboarding_completed=profile.onboarding_completed,
                profile_image_url=None,
            ),
            introduction=profile.introduction,
            career_level=profile.career_level,
            preferred_work_type=profile.preferred_work_type,
            preferred_region=profile.preferred_region,
            available_start_date=profile.available_start_date,
            available_end_date=profile.available_end_date,
            available_hours_per_week=profile.available_hours_per_week,
            profile_image_file_id=profile.profile_image_file_id,
            public_material_file_id=profile.public_material_file_id,
            external_link_url=profile.external_link_url,
            topics=ProfileService._selected_topics(db, user.user_id),
            tech_stacks=ProfileService._selected_tech_stacks(db, user.user_id),
            roles=ProfileService._selected_roles(db, user.user_id),
        )

    @staticmethod
    def _selected_topics(db: Session, user_id: int) -> list[SelectedTopic]:
        """사용자 토픽 관계를 응답 schema 목록으로 변환한다."""
        return [
            SelectedTopic(
                topic_id=topic.topic_id,
                topic_code=topic.topic_code,
                topic_name=topic.topic_name,
                is_active=topic.is_active,
                interest_level=relation.interest_level,
                priority=relation.priority,
            )
            for relation, topic in ProfileRepository.list_topics(db, user_id)
        ]

    @staticmethod
    def _selected_tech_stacks(db: Session, user_id: int) -> list[SelectedTechStack]:
        """사용자 기술 관계를 응답 schema 목록으로 변환한다."""
        return [
            SelectedTechStack(
                tech_stack_id=tech.tech_stack_id,
                tech_stack_code=tech.tech_stack_code,
                tech_stack_name=tech.tech_stack_name,
                category=tech.category,
                is_active=tech.is_active,
                proficiency_level=relation.proficiency_level,
                experience_months=relation.experience_months,
                is_learning=relation.is_learning,
            )
            for relation, tech in ProfileRepository.list_tech_stacks(db, user_id)
        ]

    @staticmethod
    def _selected_roles(db: Session, user_id: int) -> list[SelectedRole]:
        """사용자 역할 관계를 응답 schema 목록으로 변환한다."""
        return [
            SelectedRole(
                role_id=role.role_id,
                role_code=role.role_code,
                role_name=role.role_name,
                is_active=role.is_active,
                priority=relation.priority,
                experience_level=relation.experience_level,
            )
            for relation, role in ProfileRepository.list_roles(db, user_id)
        ]

    @staticmethod
    def _apply_profile_fields(profile, request, *, complete_onboarding: bool = False) -> None:
        """요청에 포함된 기본 프로필 필드를 ORM 객체에 반영한다."""
        fields = (
            "introduction",
            "career_level",
            "preferred_work_type",
            "preferred_region",
            "available_start_date",
            "available_end_date",
            "available_hours_per_week",
        )
        for field in fields:
            if field in request.model_fields_set:
                value = getattr(request, field)
                if field == "introduction" and value is not None:
                    value = re.sub(r"<[^>]*>", "", value).strip()
                setattr(profile, field, value)
        if complete_onboarding:
            profile.onboarding_completed = True
        profile.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _validate_merged_dates(profile, request: ProfileUpdateRequest) -> None:
        """부분 수정 후의 참여 가능 날짜 범위가 유효한지 확인한다."""
        start = (
            request.available_start_date
            if "available_start_date" in request.model_fields_set
            else profile.available_start_date
        )
        end = (
            request.available_end_date
            if "available_end_date" in request.model_fields_set
            else profile.available_end_date
        )
        if start and end and end < start:
            raise InvalidProfileDateRangeError
