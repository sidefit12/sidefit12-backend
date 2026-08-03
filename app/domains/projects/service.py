"""프로젝트 API 명세에 따른 비즈니스 규칙."""

import hashlib
import math
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.idempotency_requests.service import IdempotencyRequestService
from app.domains.project_applications.service import ProjectApplicationService
from app.domains.project_bookmarks.service import ProjectBookmarkService
from app.domains.project_collaboration_channels.service import ProjectCollaborationChannelService
from app.domains.project_members.service import ProjectMemberService
from app.domains.project_positions.service import ProjectPositionService
from app.domains.projects.exceptions import (
    CannotDeleteProjectWithMembersError,
    IdempotencyConflictError,
    InvalidStateTransitionError,
    ProjectNotFoundError,
    RecruitmentDeadlinePassedError,
    ReferenceNotFoundError,
    ResourceOwnershipRequiredError,
)
from app.domains.projects.models import Project
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import (
    MemberSummary,
    OwnerData,
    PageMeta,
    PositionData,
    ProjectCard,
    ProjectDetailData,
    ProjectPageData,
    ProjectStatusData,
    RoleData,
    TechStackData,
    TopicData,
)
from app.domains.roles.service import RoleService
from app.domains.tech_stacks.service import TechStackService
from app.domains.topics.service import TopicService
from app.domains.users.models import User
from app.domains.users.service import UserService


class ProjectService:
    """PROJECT-001~007, PROJECT-009의 프로젝트 규칙을 제공한다."""

    @staticmethod
    def create(
        db: Session, user: User, request, idempotency_key: str | None = None
    ) -> ProjectDetailData:
        request_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        if idempotency_key:
            existing = IdempotencyRequestService.find(db, user.user_id, idempotency_key)
            if existing:
                if existing.request_hash != request_hash:
                    raise IdempotencyConflictError()
                return ProjectService.detail(db, existing.resource_id, user, increase_view=False)
        ProjectService._validate_references(db, request)
        ProjectService._validate_deadline(request.recruitment_deadline)
        project = Project(
            owner_user_id=user.user_id,
            title=request.title.strip(),
            summary=request.summary.strip(),
            description=ProjectService._sanitize(request.description),
            work_type=request.work_type,
            region=request.region.strip() if request.region else None,
            expected_start_date=request.expected_start_date,
            expected_end_date=request.expected_end_date,
            weekly_hours=request.weekly_hours,
            recruitment_deadline=request.recruitment_deadline,
            recruitment_status="DRAFT",
            project_status="PREPARING",
            visibility=request.visibility,
            normalized_text=f"{request.title} {request.summary} {ProjectService._sanitize(request.description)}",
        )
        db.add(project)
        db.flush()
        ProjectRepository.replace_topics(db, project.project_id, request.topic_ids)
        ProjectRepository.replace_tech_stacks(db, project.project_id, request.tech_stacks)
        ProjectPositionService.replace(db, project.project_id, request.positions)
        db.flush()
        positions = ProjectPositionService.list_by_project(db, project.project_id)
        ProjectMemberService.add_owner(
            db, project.project_id, user.user_id, positions[0].project_position_id
        )
        if idempotency_key:
            IdempotencyRequestService.add(
                db, user.user_id, idempotency_key, request_hash, project.project_id
            )
        db.commit()
        return ProjectService.detail(db, project.project_id, user, increase_view=False)

    @staticmethod
    def page(
        db: Session, *, viewer: User | None = None, role_ids: list[int] | None = None, **filters
    ):
        project_ids = None
        if role_ids:
            project_ids = set()
            for role_id in role_ids:
                project_ids |= ProjectPositionService.find_project_ids_by_role(db, role_id)
        items, total = ProjectRepository.search(db, project_ids=project_ids, **filters)
        page, size = filters["page"], filters["size"]
        return ProjectPageData(
            items=[ProjectService._card(db, p, viewer) for p in items]
        ), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )

    @staticmethod
    def my_page(db: Session, user: User, **filters):
        return ProjectService.page(db, viewer=user, owner_user_id=user.user_id, **filters)

    @staticmethod
    def detail(
        db: Session, project_id: int, viewer: User | None, *, increase_view: bool = True
    ) -> ProjectDetailData:
        project = ProjectRepository.find(db, project_id)
        if (
            project is None
            or project.moderation_status == "HIDDEN"
            or (
                project.visibility == "PRIVATE"
                and (viewer is None or viewer.user_id != project.owner_user_id)
            )
        ):
            raise ProjectNotFoundError(project_id)
        if increase_view:
            project.view_count += 1
            db.commit()
        owner = UserService.get_by_id(db, project.owner_user_id)
        channels = None
        if viewer and viewer.user_id == project.owner_user_id:
            channels = [
                {
                    "channelType": c.channel_type,
                    "channelName": c.channel_name,
                    "channelUrl": c.channel_url,
                }
                for c in ProjectCollaborationChannelService.list_active_by_project(db, project_id)
            ]
        application = (
            ProjectApplicationService.find_by_user(db, project_id, viewer.user_id)
            if viewer
            else None
        )
        application_data = None
        if application is not None:
            applicant = UserService.get_by_id(db, application.applicant_user_id)
            application_data = {
                "applicationId": application.project_application_id,
                "projectId": application.project_id,
                "projectPositionId": application.project_position_id,
                "applicationMessage": application.application_message,
                "applicationStatus": application.application_status,
                "appliedAt": application.applied_at,
                "reviewedAt": application.reviewed_at,
                "rejectionReason": application.rejection_reason,
                "applicant": {"userId": applicant.user_id, "nickname": applicant.nickname},
            }
        return ProjectDetailData(
            project=ProjectService._card(db, project, viewer),
            description=project.description,
            expected_start_date=project.expected_start_date,
            expected_end_date=project.expected_end_date,
            weekly_hours=project.weekly_hours,
            visibility=project.visibility,
            updated_at=project.updated_at,
            share_url=f"https://sidefit.dev/projects/{project.project_id}",
            owner_profile={"userId": owner.user_id, "nickname": owner.nickname},
            member_summary=MemberSummary(
                total_members=ProjectMemberService.active_count(db, project_id)
            ),
            my_application=application_data,
            collaboration_channels=channels,
        )

    @staticmethod
    def update(db: Session, user: User, project_id: int, request) -> ProjectDetailData:
        project = ProjectService._owned(db, user, project_id)
        ProjectService._validate_references(db, request)
        for field in {
            "title",
            "summary",
            "description",
            "work_type",
            "region",
            "expected_start_date",
            "expected_end_date",
            "weekly_hours",
            "recruitment_deadline",
            "visibility",
        } & request.model_fields_set:
            value = getattr(request, field)
            if field == "description" and value is not None:
                value = ProjectService._sanitize(value)
            setattr(project, field, value)
        ProjectService._validate_project(project)
        if request.topic_ids is not None:
            ProjectRepository.replace_topics(db, project_id, request.topic_ids)
        if request.tech_stacks is not None:
            ProjectRepository.replace_tech_stacks(db, project_id, request.tech_stacks)
        if request.positions is not None:
            ProjectPositionService.replace(db, project_id, request.positions)
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ProjectService.detail(db, project_id, user, increase_view=False)

    @staticmethod
    def delete(db: Session, user: User, project_id: int, reason: str) -> None:
        project = ProjectRepository.find(db, project_id, include_deleted=True)
        if project is None:
            raise ProjectNotFoundError(project_id)
        if project.owner_user_id != user.user_id:
            raise ResourceOwnershipRequiredError()
        if project.deleted_at is not None:
            return
        if ProjectMemberService.has_confirmed_members(db, project_id):
            raise CannotDeleteProjectWithMembersError()
        project.deleted_at = datetime.now(timezone.utc)
        project.deleted_by_user_id = user.user_id
        project.deletion_reason = reason.strip()
        project.updated_at = project.deleted_at
        db.commit()

    @staticmethod
    def change_recruitment_status(
        db: Session, user: User, project_id: int, request
    ) -> ProjectStatusData:
        project = ProjectService._owned(db, user, project_id)
        allowed = {("DRAFT", "RECRUITING"), ("RECRUITING", "CLOSED"), ("CLOSED", "RECRUITING")}
        if project.recruitment_status == request.recruitment_status:
            return ProjectService._status(project)
        if (project.recruitment_status, request.recruitment_status) not in allowed:
            raise InvalidStateTransitionError()
        if request.recruitment_status == "RECRUITING":
            if request.new_deadline is not None:
                project.recruitment_deadline = request.new_deadline
            ProjectService._validate_deadline(project.recruitment_deadline)
            project.closed_at = None
        else:
            project.closed_at = datetime.now(timezone.utc)
        project.recruitment_status = request.recruitment_status
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ProjectService._status(project)

    @staticmethod
    def change_project_status(
        db: Session, user: User, project_id: int, request
    ) -> ProjectStatusData:
        project = ProjectService._owned(db, user, project_id)
        allowed = {
            ("PREPARING", "IN_PROGRESS"),
            ("PREPARING", "CANCELED"),
            ("IN_PROGRESS", "COMPLETED"),
            ("IN_PROGRESS", "CANCELED"),
        }
        if project.project_status == request.project_status:
            return ProjectService._status(project)
        if (project.project_status, request.project_status) not in allowed:
            raise InvalidStateTransitionError()
        project.project_status = request.project_status
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ProjectService._status(project)

    @staticmethod
    def _owned(db, user, project_id):
        project = ProjectRepository.find(db, project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        if project.owner_user_id != user.user_id:
            raise ResourceOwnershipRequiredError()
        return project

    @staticmethod
    def _validate_references(db, request):
        checks = []
        if getattr(request, "topic_ids", None) is not None:
            checks.append(("topic", set(request.topic_ids), TopicService.find_by_ids, "topic_id"))
        if getattr(request, "tech_stacks", None) is not None:
            checks.append(
                (
                    "techStack",
                    {x.tech_stack_id for x in request.tech_stacks},
                    TechStackService.find_by_ids,
                    "tech_stack_id",
                )
            )
        if getattr(request, "positions", None) is not None:
            checks.append(
                ("role", {x.role_id for x in request.positions}, RoleService.find_by_ids, "role_id")
            )
        for kind, ids, finder, key in checks:
            valid = {getattr(x, key) for x in finder(db, ids) if x.is_active}
            if ids - valid:
                raise ReferenceNotFoundError(kind, sorted(ids - valid))

    @staticmethod
    def _validate_deadline(value):
        deadline = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if deadline <= datetime.now(timezone.utc):
            raise RecruitmentDeadlinePassedError()

    @staticmethod
    def _validate_project(project):
        if (
            project.expected_start_date
            and project.expected_end_date
            and project.expected_end_date < project.expected_start_date
        ):
            raise InvalidStateTransitionError()
        if project.work_type in {"OFFLINE", "HYBRID"} and not project.region:
            raise InvalidStateTransitionError()
        ProjectService._validate_deadline(project.recruitment_deadline)

    @staticmethod
    def _sanitize(value):
        return re.sub(r"<[^>]+>", "", value).strip()

    @staticmethod
    def _status(project):
        return ProjectStatusData(
            project_id=project.project_id,
            project_status=project.project_status,
            recruitment_status=project.recruitment_status,
            updated_at=project.updated_at,
        )

    @staticmethod
    def _card(db, project, viewer):
        owner = UserService.get_by_id(db, project.owner_user_id)
        topic_rels = ProjectRepository.topics(db, project.project_id)
        topics = {
            x.topic_id: x for x in TopicService.find_by_ids(db, {r.topic_id for r in topic_rels})
        }
        tech_rels = ProjectRepository.tech_stacks(db, project.project_id)
        techs = {
            x.tech_stack_id: x
            for x in TechStackService.find_by_ids(db, {r.tech_stack_id for r in tech_rels})
        }
        positions = ProjectPositionService.list_by_project(db, project.project_id)
        accepted_counts = ProjectApplicationService.accepted_counts(db, project.project_id)
        roles = {x.role_id: x for x in RoleService.find_by_ids(db, {r.role_id for r in positions})}
        return ProjectCard(
            project_id=project.project_id,
            title=project.title,
            summary=project.summary,
            work_type=project.work_type,
            region=project.region,
            recruitment_deadline=project.recruitment_deadline,
            recruitment_status=project.recruitment_status,
            project_status=project.project_status,
            view_count=project.view_count,
            created_at=project.created_at,
            owner=OwnerData(user_id=owner.user_id, nickname=owner.nickname),
            topics=[
                TopicData(
                    topic_id=t.topic_id,
                    topic_code=t.topic_code,
                    topic_name=t.topic_name,
                    is_active=t.is_active,
                )
                for t in (topics[r.topic_id] for r in topic_rels)
            ],
            tech_stacks=[
                TechStackData(
                    tech_stack_id=t.tech_stack_id,
                    tech_stack_code=t.tech_stack_code,
                    tech_stack_name=t.tech_stack_name,
                    category=t.category,
                    is_active=t.is_active,
                )
                for t in (techs[r.tech_stack_id] for r in tech_rels)
            ],
            positions=[
                PositionData(
                    project_position_id=p.project_position_id,
                    position_title=p.position_title,
                    required_count=p.required_count,
                    accepted_count=accepted_counts.get(p.project_position_id, 0),
                    position_status=p.position_status,
                    responsibilities=p.responsibilities,
                    required_level=p.required_level,
                    role=RoleData(
                        role_id=roles[p.role_id].role_id,
                        role_code=roles[p.role_id].role_code,
                        role_name=roles[p.role_id].role_name,
                        is_active=roles[p.role_id].is_active,
                    ),
                )
                for p in positions
            ],
            is_applied=(
                ProjectApplicationService.find_by_user(db, project.project_id, viewer.user_id)
                is not None
            )
            if viewer
            else None,
            is_bookmarked=ProjectBookmarkService.exists(db, viewer.user_id, project.project_id)
            if viewer
            else None,
        )
