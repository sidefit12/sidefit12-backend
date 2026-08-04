"""신고 생성과 관리자 처리 비즈니스 규칙."""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.projects.schemas import PageMeta
from app.domains.projects.service import ProjectService
from app.domains.reports.exceptions import (
    AdminRoleRequiredError,
    CannotReportOwnResourceError,
    CannotReportSelfError,
    DuplicateReportError,
    InvalidReportQueryError,
    ReportAlreadyProcessedError,
    ReportInvalidStateError,
    ReportNotFoundError,
    ReportUserNotFoundError,
)
from app.domains.reports.repository import ReportRepository
from app.domains.reports.schemas import (
    AdminReportDetail,
    AdminUserSummary,
    ReportPageData,
    ReportResource,
)
from app.domains.user_profiles.service import ProfileService
from app.domains.users.models import User
from app.domains.users.service import UserService


class ReportService:
    @staticmethod
    def report_project(db: Session, user: User, project_id: int, request):
        project = ProjectService.find_or_raise_visible(db, project_id, user)
        if project.owner_user_id == user.user_id:
            raise CannotReportOwnResourceError()
        return ReportService._create(db, user, "PROJECT", project_id, request)

    @staticmethod
    def report_user(db: Session, user: User, target_user_id: int, request):
        if user.user_id == target_user_id:
            raise CannotReportSelfError()
        if UserService.get_by_id(db, target_user_id) is None:
            raise ReportUserNotFoundError()
        return ReportService._create(db, user, "USER", target_user_id, request)

    @staticmethod
    def _create(db, user, target_type, target_id, request):
        if ReportRepository.active_duplicate(db, user.user_id, target_type, target_id):
            raise DuplicateReportError()
        report = ReportRepository.add(
            db,
            reporter_id=user.user_id,
            target_type=target_type,
            target_id=target_id,
            request=request,
        )
        db.commit()
        return ReportService._resource(report)

    @staticmethod
    def admin_page(db, admin, **filters):
        ReportService._require_admin(admin)
        if filters["from_at"] and filters["to_at"] and filters["to_at"] < filters["from_at"]:
            raise InvalidReportQueryError()
        items, total = ReportRepository.page(db, **filters)
        size, page = filters["size"], filters["page"]
        return ReportPageData(items=[ReportService._resource(x) for x in items]), PageMeta(
            page=page,
            size=size,
            total_elements=total,
            total_pages=math.ceil(total / size) if total else 0,
            has_next=(page + 1) * size < total,
        )

    @staticmethod
    def admin_detail(db, admin, report_id):
        ReportService._require_admin(admin)
        report = ReportRepository.find(db, report_id)
        if report is None:
            raise ReportNotFoundError()
        return ReportService._detail(db, report)

    @staticmethod
    def process(db, admin, report_id, request):
        ReportService._require_admin(admin)
        report = ReportRepository.find(db, report_id, lock=True)
        if report is None:
            raise ReportNotFoundError()
        if report.report_status in {"RESOLVED", "REJECTED"}:
            raise ReportAlreadyProcessedError()
        if request.report_status not in {"IN_REVIEW", "RESOLVED", "REJECTED"}:
            raise ReportInvalidStateError()
        action = request.action or "NONE"
        if action == "HIDE_PROJECT":
            if report.target_type != "PROJECT":
                raise ReportInvalidStateError()
            ProjectService.hide_by_admin(db, report.target_project_id)
        elif action == "SUSPEND_USER":
            if report.target_type != "USER":
                raise ReportInvalidStateError()
            target = UserService.get_by_id(db, report.target_user_id)
            if target is None:
                raise ReportNotFoundError()
            UserService.suspend(target)
        report.report_status = request.report_status
        report.resolution_note = request.resolution_note.strip()
        report.handled_by_user_id = admin.user_id
        report.handled_at = datetime.now(timezone.utc)
        db.commit()
        return ReportService._detail(db, report)

    @staticmethod
    def _require_admin(user):
        if user.system_role != "ADMIN":
            raise AdminRoleRequiredError()

    @staticmethod
    def _resource(report):
        return ReportResource.model_validate(report)

    @staticmethod
    def _user(db, user):
        profile = ProfileService.get_user_summary(db, user.user_id)
        return AdminUserSummary(
            user_id=user.user_id,
            nickname=user.nickname,
            user_status=user.user_status,
            system_role=user.system_role,
            onboarding_completed=bool(profile["onboarding_completed"]),
            profile_image_url=profile["profile_image_url"],
            email=user.email,
        )

    @staticmethod
    def _detail(db, report):
        reporter = UserService.get_by_id(db, report.reporter_user_id)
        handler = (
            UserService.get_by_id(db, report.handled_by_user_id)
            if report.handled_by_user_id
            else None
        )
        if report.target_type == "PROJECT":
            project = ProjectService.find_for_admin(db, report.target_project_id)
            target = {
                "projectId": project.project_id,
                "title": project.title,
                "visibility": project.visibility,
                "moderationStatus": project.moderation_status,
            }
        else:
            user = UserService.get_by_id(db, report.target_user_id)
            target = {
                "userId": user.user_id,
                "nickname": user.nickname,
                "userStatus": user.user_status,
            }
        return AdminReportDetail(
            report=ReportService._resource(report),
            reporter=ReportService._user(db, reporter),
            target=target,
            handled_by=ReportService._user(db, handler) if handler else None,
            handled_at=report.handled_at,
        )
