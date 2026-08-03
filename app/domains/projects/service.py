"""프로젝트 모집과 조회·수정 비즈니스 규칙."""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.project_collaboration_channels.service import (
    ProjectCollaborationChannelService,
)
from app.domains.project_positions.service import ProjectPositionService
from app.domains.projects.exceptions import (
    InvalidProjectSelectionError,
    InvalidProjectStateError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)
from app.domains.projects.models import Project
from app.domains.projects.repository import ProjectRepository
from app.domains.projects.schemas import (
    CollaborationChannelData,
    OwnerData,
    PositionData,
    ProjectData,
    ProjectDeleteData,
    ProjectListData,
    TechStackData,
    TopicData,
)
from app.domains.roles.service import RoleService
from app.domains.tech_stacks.service import TechStackService
from app.domains.topics.service import TopicService
from app.domains.users.models import User
from app.domains.users.service import UserService


class ProjectService:
    @staticmethod
    def create(db: Session, user: User, request) -> ProjectData:
        ProjectService._validate_selections(db, request)
        now = datetime.now(timezone.utc)
        if request.recruitment_status == "RECRUITING" and request.recruitment_deadline <= now:
            raise InvalidProjectStateError("모집 중 프로젝트의 마감일은 현재보다 이후여야 합니다.")
        values = request.model_dump(
            exclude={"topics", "tech_stacks", "positions", "collaboration_channels"}
        )
        project = Project(
            owner_user_id=user.user_id,
            **values,
            normalized_text=ProjectService._normalized(request),
        )
        db.add(project)
        db.flush()
        ProjectService._replace_relations(db, project.project_id, user.user_id, request)
        db.commit()
        return ProjectService.get(db, project.project_id, user)

    @staticmethod
    def get(db: Session, project_id: int, viewer: User | None = None) -> ProjectData:
        project = ProjectRepository.find(db, project_id)
        if project is None or (
            project.visibility == "PRIVATE"
            and (viewer is None or viewer.user_id != project.owner_user_id)
        ):
            raise ProjectNotFoundError(project_id)
        return ProjectService._data(db, project)

    @staticmethod
    def list(db: Session, **filters) -> ProjectListData:
        role_id = filters.pop("role_id")
        filters["project_ids"] = (
            ProjectPositionService.find_project_ids_by_role(db, role_id)
            if role_id is not None
            else None
        )
        items, total = ProjectRepository.list(db, **filters)
        size = filters["size"]
        return ProjectListData(
            items=[ProjectService._data(db, item) for item in items],
            page=filters["page"],
            size=size,
            total=total,
            total_pages=math.ceil(total / size) if total else 0,
        )

    @staticmethod
    def update(db: Session, user: User, project_id: int, request) -> ProjectData:
        project = ProjectService._owned(db, user, project_id)
        if (
            request.topics is not None
            or request.tech_stacks is not None
            or request.positions is not None
        ):
            ProjectService._validate_selections(db, request)
        fields = {
            "title",
            "summary",
            "description",
            "work_type",
            "region",
            "expected_start_date",
            "expected_end_date",
            "weekly_hours",
            "recruitment_deadline",
            "recruitment_status",
            "project_status",
            "visibility",
        }
        for field in fields & request.model_fields_set:
            setattr(project, field, getattr(request, field))
        ProjectService._validate_merged(project)
        if project.recruitment_status == "CLOSED" and project.closed_at is None:
            project.closed_at = datetime.now(timezone.utc)
        elif project.recruitment_status != "CLOSED":
            project.closed_at = None
        if request.topics is not None:
            ProjectRepository.replace_topics(db, project_id, request.topics)
        if request.tech_stacks is not None:
            ProjectRepository.replace_tech_stacks(db, project_id, request.tech_stacks)
        if request.positions is not None:
            ProjectPositionService.replace(db, project_id, request.positions)
        if request.collaboration_channels is not None:
            ProjectCollaborationChannelService.replace(
                db, project_id, user.user_id, request.collaboration_channels
            )
        project.normalized_text = f"{project.title} {project.summary} {project.description}".strip()
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        return ProjectService.get(db, project_id, user)

    @staticmethod
    def delete(db: Session, user: User, project_id: int, reason: str) -> ProjectDeleteData:
        project = ProjectService._owned(db, user, project_id)
        project.deleted_at = datetime.now(timezone.utc)
        project.deleted_by_user_id = user.user_id
        project.deletion_reason = reason.strip()
        project.updated_at = project.deleted_at
        db.commit()
        return ProjectDeleteData(project_id=project_id)

    @staticmethod
    def _owned(db: Session, user: User, project_id: int) -> Project:
        project = ProjectRepository.find(db, project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        if project.owner_user_id != user.user_id:
            raise ProjectPermissionDeniedError()
        return project

    @staticmethod
    def _validate_selections(db: Session, request) -> None:
        checks = []
        if getattr(request, "topics", None) is not None:
            checks.append(("topic", {x.topic_id for x in request.topics}, TopicService.find_by_ids))
        if getattr(request, "tech_stacks", None) is not None:
            checks.append(
                (
                    "techStack",
                    {x.tech_stack_id for x in request.tech_stacks},
                    TechStackService.find_by_ids,
                )
            )
        if getattr(request, "positions", None) is not None:
            checks.append(("role", {x.role_id for x in request.positions}, RoleService.find_by_ids))
        for item_type, ids, finder in checks:
            found = finder(db, ids)
            valid = {
                next(v for k, v in vars(item).items() if k.endswith("_id"))
                for item in found
                if item.is_active
            }
            invalid = sorted(ids - valid)
            if invalid:
                raise InvalidProjectSelectionError(item_type, invalid)

    @staticmethod
    def _replace_relations(db: Session, project_id: int, user_id: int, request) -> None:
        ProjectRepository.replace_topics(db, project_id, request.topics)
        ProjectRepository.replace_tech_stacks(db, project_id, request.tech_stacks)
        ProjectPositionService.replace(db, project_id, request.positions)
        ProjectCollaborationChannelService.replace(
            db, project_id, user_id, request.collaboration_channels
        )

    @staticmethod
    def _validate_merged(project: Project) -> None:
        if (
            project.expected_start_date
            and project.expected_end_date
            and project.expected_end_date < project.expected_start_date
        ):
            raise InvalidProjectStateError("예상 종료일은 예상 시작일보다 빠를 수 없습니다.")
        if project.work_type == "OFFLINE" and not (project.region and project.region.strip()):
            raise InvalidProjectStateError("오프라인 프로젝트에는 지역이 필요합니다.")
        deadline = project.recruitment_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if project.recruitment_status == "RECRUITING" and deadline <= datetime.now(timezone.utc):
            raise InvalidProjectStateError("모집 중 프로젝트의 마감일은 현재보다 이후여야 합니다.")

    @staticmethod
    def _normalized(request) -> str:
        return f"{request.title} {request.summary} {request.description}".strip()

    @staticmethod
    def _data(db: Session, project: Project) -> ProjectData:
        owner = UserService.get_by_id(db, project.owner_user_id)
        topic_relations = ProjectRepository.topics(db, project.project_id)
        topics = {
            item.topic_id: item
            for item in TopicService.find_by_ids(db, {item.topic_id for item in topic_relations})
        }
        tech_relations = ProjectRepository.tech_stacks(db, project.project_id)
        tech_stacks = {
            item.tech_stack_id: item
            for item in TechStackService.find_by_ids(
                db, {item.tech_stack_id for item in tech_relations}
            )
        }
        position_relations = ProjectPositionService.list_by_project(db, project.project_id)
        roles = {
            item.role_id: item
            for item in RoleService.find_by_ids(db, {item.role_id for item in position_relations})
        }
        return ProjectData(
            project_id=project.project_id,
            owner=OwnerData(user_id=owner.user_id, nickname=owner.nickname),
            title=project.title,
            summary=project.summary,
            description=project.description,
            work_type=project.work_type,
            region=project.region,
            expected_start_date=project.expected_start_date,
            expected_end_date=project.expected_end_date,
            weekly_hours=project.weekly_hours,
            recruitment_deadline=project.recruitment_deadline,
            recruitment_status=project.recruitment_status,
            project_status=project.project_status,
            visibility=project.visibility,
            view_count=project.view_count,
            closed_at=project.closed_at,
            created_at=project.created_at,
            updated_at=project.updated_at,
            topics=[
                TopicData(
                    topic_id=topics[r.topic_id].topic_id,
                    topic_code=topics[r.topic_id].topic_code,
                    topic_name=topics[r.topic_id].topic_name,
                    is_primary=r.is_primary,
                )
                for r in topic_relations
            ],
            tech_stacks=[
                TechStackData(
                    tech_stack_id=tech_stacks[r.tech_stack_id].tech_stack_id,
                    tech_stack_code=tech_stacks[r.tech_stack_id].tech_stack_code,
                    tech_stack_name=tech_stacks[r.tech_stack_id].tech_stack_name,
                    requirement_type=r.requirement_type,
                    required_level=r.required_level,
                )
                for r in tech_relations
            ],
            positions=[
                PositionData(
                    project_position_id=r.project_position_id,
                    role_id=roles[r.role_id].role_id,
                    role_code=roles[r.role_id].role_code,
                    role_name=roles[r.role_id].role_name,
                    position_title=r.position_title,
                    responsibilities=r.responsibilities,
                    required_count=r.required_count,
                    required_level=r.required_level,
                    position_status=r.position_status,
                )
                for r in position_relations
            ],
            collaboration_channels=[
                CollaborationChannelData.model_validate(c)
                for c in ProjectCollaborationChannelService.list_active_by_project(
                    db, project.project_id
                )
            ],
        )
