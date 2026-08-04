"""프로젝트 지원 생성, 조회, 취소 및 심사 비즈니스 로직."""

import hashlib
import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.idempotency_requests.service import IdempotencyRequestService
from app.domains.notifications.service import NotificationService
from app.domains.project_applications.exceptions import (
    AlreadyAppliedError,
    ApplicationAccessDeniedError,
    ApplicationAlreadyProcessedError,
    ApplicationIdempotencyConflictError,
    ApplicationNotFoundError,
    CannotApplyOwnProjectError,
    PositionCapacityExceededError,
    PositionClosedError,
    RecruitmentClosedError,
)
from app.domains.project_applications.repository import ProjectApplicationRepository
from app.domains.project_applications.schemas import (
    ApplicantSummary,
    ApplicationDecisionData,
    ApplicationDetailData,
    ApplicationPageData,
    ApplicationResource,
    MemberResource,
    MemberUserSummary,
    PageMeta,
    PositionSummary,
)
from app.domains.project_members.service import ProjectMemberService
from app.domains.project_positions.service import ProjectPositionService
from app.domains.projects.repository import ProjectRepository
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User
from app.domains.users.service import UserService


class ProjectApplicationService:
    """APP-001~007의 프로젝트 지원 규칙을 제공한다."""

    @staticmethod
    def find_by_user(db: Session, project_id: int, user_id: int):
        return ProjectApplicationRepository.find_by_user(db, project_id, user_id)

    @staticmethod
    def accepted_counts(db: Session, project_id: int) -> dict[int, int]:
        return ProjectApplicationRepository.accepted_counts(db, project_id)

    @staticmethod
    def status_counts_by_user(db: Session, user_id: int) -> dict[str, int]:
        """홈 활동 요약에 사용자 지원 상태별 개수를 제공한다."""
        return ProjectApplicationRepository.status_counts(db, user_id=user_id)

    @staticmethod
    def create(
        db: Session,
        user: User,
        project_id: int,
        request,
        idempotency_key: str | None = None,
    ) -> ApplicationResource:
        """모집 상태와 포지션을 검증하고 지원을 생성하거나 취소 건을 재활성화한다."""
        from app.domains.projects.service import ProjectService

        request_hash = hashlib.sha256(
            f"application:{project_id}:{request.model_dump_json()}".encode()
        ).hexdigest()
        if idempotency_key:
            previous = IdempotencyRequestService.find(db, user.user_id, idempotency_key)
            if previous:
                if previous.request_hash != request_hash:
                    raise ApplicationIdempotencyConflictError()
                application = ProjectApplicationRepository.find(db, previous.resource_id)
                if application is not None:
                    return ProjectApplicationService._resource(db, application)

        project = ProjectService.get_for_application(db, project_id)
        if project.owner_user_id == user.user_id:
            raise CannotApplyOwnProjectError()
        if project.recruitment_status != "RECRUITING" or ProjectApplicationService._expired(
            project.recruitment_deadline
        ):
            raise RecruitmentClosedError()

        position = ProjectPositionService.find(db, request.project_position_id)
        if (
            position is None
            or position.project_id != project_id
            or position.position_status != "OPEN"
        ):
            raise PositionClosedError()

        application = ProjectApplicationRepository.find_by_user(db, project_id, user.user_id)
        if application is not None and application.application_status != "CANCELED":
            raise AlreadyAppliedError()

        now = datetime.now(timezone.utc)
        if application is None:
            application = ProjectApplicationRepository.add(
                db,
                project_id=project_id,
                position_id=request.project_position_id,
                applicant_user_id=user.user_id,
                message=request.application_message.strip(),
            )
        else:
            application.project_position_id = request.project_position_id
            application.application_message = request.application_message.strip()
            application.application_status = "PENDING"
            application.applied_at = now
            application.reviewed_by_user_id = None
            application.reviewed_at = None
            application.canceled_at = None
            application.rejection_reason = None
        NotificationService.application_received(
            db, project.owner_user_id, application.project_application_id
        )
        if idempotency_key:
            IdempotencyRequestService.add(
                db,
                user.user_id,
                idempotency_key,
                request_hash,
                application.project_application_id,
            )
        db.commit()
        return ProjectApplicationService._resource(db, application)

    @staticmethod
    def my_page(db: Session, user: User, *, page: int, size: int, status: str | None):
        """현재 사용자의 지원 목록과 전체 상태 집계를 반환한다."""
        items, total = ProjectApplicationRepository.page_by_user(
            db, user.user_id, page=page, size=size, status=status
        )
        counts = ProjectApplicationRepository.status_counts(db, user_id=user.user_id)
        return ProjectApplicationService._page_result(db, items, counts, page, size, total)

    @staticmethod
    def project_page(
        db: Session,
        user: User,
        project_id: int,
        *,
        page: int,
        size: int,
        status: str | None,
        position_id: int | None,
    ):
        """프로젝트 소유자에게 지원자 목록과 상태 집계를 반환한다."""
        from app.domains.projects.service import ProjectService

        ProjectService.require_owner(db, user, project_id)
        if position_id is not None:
            position = ProjectPositionService.find(db, position_id)
            if position is None or position.project_id != project_id:
                raise PositionClosedError()
        items, total = ProjectApplicationRepository.page_by_project(
            db,
            project_id,
            page=page,
            size=size,
            status=status,
            position_id=position_id,
        )
        counts = ProjectApplicationRepository.status_counts(db, project_id=project_id)
        return ProjectApplicationService._page_result(db, items, counts, page, size, total)

    @staticmethod
    def detail(db: Session, user: User, application_id: int) -> ApplicationDetailData:
        """지원자 또는 프로젝트 소유자에게 지원 상세와 공개 프로필을 반환한다."""
        from app.domains.projects.service import ProjectService

        application = ProjectApplicationRepository.find(db, application_id)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        project = ProjectService.get_for_application(db, application.project_id)
        if user.user_id not in {application.applicant_user_id, project.owner_user_id}:
            raise ApplicationAccessDeniedError()
        return ApplicationDetailData(
            applicant_profile=ProfileService.get_public_profile(db, application.applicant_user_id),
            application=ProjectApplicationService._resource(db, application),
            submitted_snapshot=None,
        )

    @staticmethod
    def cancel(db: Session, user: User, application_id: int, _reason: str | None):
        """지원자 본인의 대기 지원을 취소한다."""
        application = ProjectApplicationRepository.find(db, application_id, lock=True)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        if application.applicant_user_id != user.user_id:
            raise ApplicationAccessDeniedError()
        if application.application_status == "CANCELED":
            return ProjectApplicationService._resource(db, application)
        if application.application_status != "PENDING":
            raise ApplicationAlreadyProcessedError()
        application.application_status = "CANCELED"
        application.canceled_at = datetime.now(timezone.utc)
        db.commit()
        return ProjectApplicationService._resource(db, application)

    @staticmethod
    def accept(db: Session, user: User, application_id: int, _note: str | None):
        """프로젝트 소유자가 대기 지원을 승인하고 팀원을 생성한다."""
        from app.domains.projects.service import ProjectService

        application = ProjectApplicationRepository.find(db, application_id, lock=True)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        ProjectService.require_owner(db, user, application.project_id)
        if application.application_status == "ACCEPTED":
            return ProjectApplicationService._decision(db, application)
        if application.application_status != "PENDING":
            raise ApplicationAlreadyProcessedError()

        position = ProjectPositionService.find(db, application.project_position_id, lock=True)
        accepted = ProjectApplicationRepository.accepted_counts(db, application.project_id).get(
            application.project_position_id, 0
        )
        if (
            position is None
            or position.position_status != "OPEN"
            or accepted >= position.required_count
        ):
            raise PositionCapacityExceededError()

        now = datetime.now(timezone.utc)
        application.application_status = "ACCEPTED"
        application.reviewed_by_user_id = user.user_id
        application.reviewed_at = now
        member = ProjectMemberService.add_accepted_member(
            db,
            project_id=application.project_id,
            user_id=application.applicant_user_id,
            position_id=application.project_position_id,
            application_id=application.project_application_id,
            actor_user_id=user.user_id,
        )
        if accepted + 1 >= position.required_count:
            ProjectPositionService.close(db, position)
        NotificationService.application_decided(
            db,
            application.applicant_user_id,
            application.project_application_id,
            accepted=True,
        )
        db.commit()
        return ProjectApplicationService._decision(db, application, member)

    @staticmethod
    def reject(db: Session, user: User, application_id: int, request):
        """프로젝트 소유자가 대기 지원을 거절한다."""
        from app.domains.projects.service import ProjectService

        application = ProjectApplicationRepository.find(db, application_id, lock=True)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        ProjectService.require_owner(db, user, application.project_id)
        if application.application_status == "REJECTED":
            return ProjectApplicationService._decision(db, application)
        if application.application_status != "PENDING":
            raise ApplicationAlreadyProcessedError()
        reason = request.rejection_reason_code
        if request.rejection_reason:
            reason = f"{reason}: {request.rejection_reason.strip()}"
        application.application_status = "REJECTED"
        application.reviewed_by_user_id = user.user_id
        application.reviewed_at = datetime.now(timezone.utc)
        application.rejection_reason = reason[:500]
        NotificationService.application_decided(
            db,
            application.applicant_user_id,
            application.project_application_id,
            accepted=False,
        )
        db.commit()
        return ProjectApplicationService._decision(db, application)

    @staticmethod
    def _resource(
        db: Session, application, *, project_title: str | None = None
    ) -> ApplicationResource:
        applicant = UserService.get_by_id(db, application.applicant_user_id)
        if project_title is None:
            project = ProjectRepository.find(db, application.project_id, include_deleted=True)
            project_title = project.title if project is not None else ""
        return ApplicationResource(
            application_id=application.project_application_id,
            project_id=application.project_id,
            project_title=project_title,
            project_position_id=application.project_position_id,
            application_message=application.application_message,
            application_status=application.application_status,
            applied_at=application.applied_at,
            reviewed_at=application.reviewed_at,
            rejection_reason=application.rejection_reason,
            applicant=ApplicantSummary(user_id=applicant.user_id, nickname=applicant.nickname),
        )

    @staticmethod
    def _page_result(db, items, counts, page, size, total):
        project_titles = ProjectRepository.titles_by_ids(db, {item.project_id for item in items})
        return ApplicationPageData(
            items=[
                ProjectApplicationService._resource(
                    db,
                    item,
                    project_title=project_titles.get(item.project_id, ""),
                )
                for item in items
            ],
            status_counts=counts,
        ), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )

    @staticmethod
    def _decision(db, application, member=None) -> ApplicationDecisionData:
        position = ProjectPositionService.find(db, application.project_position_id)
        accepted = ProjectApplicationRepository.accepted_counts(db, application.project_id).get(
            application.project_position_id, 0
        )
        member_data = None
        if member is not None:
            user = UserService.get_by_id(db, member.user_id)
            profile = ProfileService.get_user_summary(db, user.user_id)
            member_data = MemberResource(
                project_member_id=member.project_member_id,
                project_id=member.project_id,
                project_position_id=member.project_position_id,
                member_type=member.member_type,
                member_status=member.member_status,
                joined_at=member.joined_at,
                left_at=member.left_at,
                user=MemberUserSummary(
                    user_id=user.user_id,
                    nickname=user.nickname,
                    user_status=user.user_status,
                    system_role=user.system_role,
                    onboarding_completed=bool(profile["onboarding_completed"]),
                    profile_image_url=profile["profile_image_url"],
                ),
            )
        return ApplicationDecisionData(
            application=ProjectApplicationService._resource(db, application),
            member=member_data,
            position_summary=PositionSummary(
                required_count=position.required_count,
                accepted_count=accepted,
                position_status=position.position_status,
            ),
        )

    @staticmethod
    def _expired(deadline: datetime) -> bool:
        value = deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)
        return value <= datetime.now(timezone.utc)
