"""신고 데이터 접근 계층."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.reports.models import Report


class ReportRepository:
    @staticmethod
    def find(db: Session, report_id: int, *, lock: bool = False):
        query = select(Report).where(Report.report_id == report_id)
        if lock:
            query = query.with_for_update()
        return db.scalar(query)

    @staticmethod
    def active_duplicate(db, reporter_id, target_type, target_id):
        target = Report.target_user_id if target_type == "USER" else Report.target_project_id
        return db.scalar(
            select(Report).where(
                Report.reporter_user_id == reporter_id,
                Report.target_type == target_type,
                target == target_id,
                Report.report_status.in_(["PENDING", "IN_REVIEW"]),
            )
        )

    @staticmethod
    def add(db, *, reporter_id, target_type, target_id, request):
        report = Report(
            reporter_user_id=reporter_id,
            target_type=target_type,
            target_user_id=target_id if target_type == "USER" else None,
            target_project_id=target_id if target_type == "PROJECT" else None,
            reason_type=request.reason_type,
            detail=request.detail.strip() if request.detail else None,
        )
        db.add(report)
        db.flush()
        return report

    @staticmethod
    def page(db, *, page, size, status, target_type, from_at, to_at):
        query = select(Report)
        count = select(func.count()).select_from(Report)
        filters = []
        if status:
            filters.append(Report.report_status == status)
        if target_type:
            filters.append(Report.target_type == target_type)
        if from_at:
            filters.append(Report.created_at >= from_at)
        if to_at:
            filters.append(Report.created_at <= to_at)
        query = query.where(*filters)
        count = count.where(*filters)
        total = db.scalar(count) or 0
        return list(
            db.scalars(
                query.order_by(Report.created_at.desc()).offset(page * size).limit(size)
            ).all()
        ), total
